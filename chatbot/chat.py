import os
import logging
import ast
from langchain.globals import set_debug, set_verbose
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import ChatOpenAI
#from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.vectorstores import SQLiteVec
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langgraph.graph import START, END, StateGraph
from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver

from typing import Literal
from typing_extensions import List, TypedDict
from typing_extensions import Annotated

DB_PATH = os.getenv("DB_PATH", "static/database")
os.makedirs(DB_PATH, exist_ok = True)

DB_VEC_SQLITE_FILE = os.getenv("DB_SQLITE_FILE", "vec.db")
DB_SQLITE_FILE = os.getenv("DB_SQLITE_FILE", "database.db")

# generate logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.environ.get("OPENAI_API_KEY"):
  raise Exception("Environment OPENAI_API_KEY needs to be set.")

set_debug(False)
set_verbose(False)

llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatOpenAI(model="gpt-4o")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

#vector_store = InMemoryVectorStore(embeddings)
vector_store = SQLiteVec(table = "products_emb", connection = None, embedding = embeddings, db_file = os.path.join(DB_PATH, DB_VEC_SQLITE_FILE))

db = SQLDatabase.from_uri("sqlite:///" + os.path.join(DB_PATH, DB_SQLITE_FILE))

def string_to_list_of_tuples(string):
    """Converts a string representation of a list of tuples to a list of tuples."""
    return ast.literal_eval(string)

def init_vectore_store(database):
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    products, metas = database.products_as_documents()

    docs = text_splitter.create_documents(
        products, metadatas=metas
    )

    all_splits = text_splitter.split_documents(docs)

    vector_store.add_documents(documents=all_splits)


ragTemplate = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use five sentences maximum and keep the answer as concise as possible.
Always ask if more details on the response, suggestions or other options are needed at the end of the answer.

{context}

Question: {question}

Helpful Answer:"""

ordersSqlTemplate = """
Given an input question, create a syntactically correct {dialect} query to run to help find the answer. 

You can order the results by a relevant column to return the most interesting examples in the database.

Always include the date, order time, customer id, shipping cost, product and sales amount besides the relevant columns given the question.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. 
Also, pay attention to which column is in which table.

Only use the following tables:
{table_info}

Question: {input}
"""

myOrdersSqlTemplate = """
Given an input question, create a syntactically correct {dialect} query to run to help find the answer and selects all rows, with no limit.

Always include the date, order time, shipping cost, product and sales amount besides the relevant columns given the question.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. 
If the customer id is not part of the input use 'YOUR_CUSTOMER_ID' instead. 

Only use the following tables:
{table_info}

Question: {input}
"""

myOneOrderSqlTemplate = """
Given an input question, create a syntactically correct {dialect} query to run to help find the answer. 

Always include the date, order time, shipping cost, product and sales amount besides the relevant columns given the question.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. 
If the customer id is not part of the input use 'YOUR_CUSTOMER_ID' instead. Limit selection to 1 based on customer order.

Only use the following tables:
{table_info}

Question: {input}
"""

orderSqlResponseTemplate = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question. Use the template given in the example.\n\n"
        'Question: {question}\n'
        'SQL Query: {sqlQuery}\n'
        'SQL Result: {sqlResult}\n\n'
        'Example: \n1. On December 30, 2018, Car Pillow & Neck Rest was ordered for $231 with a shipping'
        'cost of $14.20. (Customer ID: 36086).\n'
        '2. Also on December 30, 2018, Car Seat Covers were ordered for $114 with a shipping'
        'cost of $1.10. (Customer ID: 35081).\n'
        '3. On the same day, Tyre was ordered for $250 with a shipping cost of $13.30. (Customer'
        'ID: 26306).\n'
        '4. Another order for Car Pillow & Neck Rest was placed for $231 with a shipping cost of'
        '$10.50. (Customer ID: 50454).\n'
        '5. Finally, on December 30, 2018, Car & Bike Care was ordered for $118 with a shipping'
        'cost of $2.90. (Customer ID: 41577).\n\n'
        'Let me know if you''d like more details about any of these orders!'
    )

askForCustomerIdTemplate = (
        "Based on the example below, ask the customer to provide the Customer ID specific to user input.\n\n"
        "user input: {user_input}\n\n"
        "Example: Please provide your Customer ID to retrieve your cell-phone order."
    )

noDataFoundTemplate= (
        "For the customer request below inform the user that no data has been found. Customer can start over with different information.\n\n"
        "Customer request:\n"
        "{user_input}"
    )

orderResultTemplate = (
        "Given the following user question, the corresponding SQL query, "
        "and SQL result, answer the user question using the example below.\n\n"
        'Question: {user_input}\n'
        'SQL Query: {sqlQuery}\n'
        'SQL Result: {sql_result}\n\n'
        "Example: Your order for one Samsung mobile phone placed on 2018-06-14 has a Medium\n"
        "priority and cost you $220 plus $13.8 shipping. \n"
        "Let me know if you'd like more details or need assistance with this order."
    )

askUserToPickOneRowTemplate = (
        "The user question has multiple ({len_rows}) rows instead of one. Based on the user question and the returned data\n"
        "ask the user to select a specific row based on the example below.\n"
        'Question: {user_input}\n'
        'SQL Query: {sqlQuery}\n'
        'rows: {sqlResult}\n\n'
        "Example: You have two orders for samsung mobile phones: one placed on 2018-06-14 with "
        "another placed on 2018-08-08. Which order would you like to inquire about?\n\n"
        "Helpful answer:\n"
    )

otherTopicTemplate = """
Ask the user politely to change the input below to query (musical) products or personal orders instead of generic queries.


User input: {user_input}

Helpful answer:
"""

custom_rag_prompt = PromptTemplate.from_template(ragTemplate)
custom_order_sql_prompt = PromptTemplate.from_template(ordersSqlTemplate)
custom_my_order_sql_prompt = PromptTemplate.from_template(myOrdersSqlTemplate)
custom_my_one_order_sql_prompt = PromptTemplate.from_template(myOneOrderSqlTemplate)
custom_order_sql_response_prompt = PromptTemplate.from_template(orderSqlResponseTemplate)
custom_ask_for_id_prompt = PromptTemplate.from_template(askForCustomerIdTemplate)
custom_no_data_found_prompt = PromptTemplate.from_template(noDataFoundTemplate)
custom_order_result_prompt = PromptTemplate.from_template(orderResultTemplate)
custom_pick_one_order_prompt = PromptTemplate.from_template(askUserToPickOneRowTemplate)
custom_other_topic_prompt = PromptTemplate.from_template(otherTopicTemplate)

# Pydantic techniques
# implicit :(
class QueryData(TypedDict):
    """main topic of the user input"""

    source: Annotated[
        Literal["order", "product", "other"],
        ...,
        "topic of the given given question",
    ]

class NeedsCustomerId(TypedDict):
    """ order question about a specific customer ID """

    orderScope: Annotated[
        Literal["my orders", "all orders"],
        ...,
        "Scope of the order question: about my orders or on all orders"
    ]

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

# Define state for application
class State(TypedDict):
    question: str
    queryData: QueryData
    needsCustomerId: NeedsCustomerId
    customerOrder: str
    sqlQuery: QueryOutput
    sqlResult: any
    context: List[Document]
    myOrderQuestions: List[str]
    answer: str


# pydentic detection of the input type => order or product related?
def detect_question_type(state: State):
    if "myOrderQuestions" not in state or len(state["myOrderQuestions"]) == 0:
        structured_llm = llm.with_structured_output(QueryData)
        query = structured_llm.invoke(state["question"])
        #logger.info(str(query))
        return {"queryData": query}
    else:
        return {"queryData": state["queryData"]}

# pydentic detection of an order input for my orders or all orders
def analyze_need_for_customer_id(state: State):
    if "myOrderQuestions" not in state or len(state["myOrderQuestions"]) == 0:
        structured_llm = llm.with_structured_output(NeedsCustomerId)
        query = structured_llm.invoke(state["question"])
        return {"needsCustomerId": query}
    else:
        return {"needsCustomerId": state["needsCustomerId"]}

# condition node, split between order types
def my_order_or_all_orders(state: State) -> Literal["all orders", "my orders"]:
    if "myOrderQuestions" not in state or len(state["myOrderQuestions"]) == 0:
        if state["needsCustomerId"]["orderScope"] == "all orders":
            return "all orders"
    return "my orders"

# condition node for split between product input type and order input type
def product_or_order(state: State) -> Literal["product", "order", "other"]:
    if state["queryData"]["source"] == "order":
        return "order"
    if state["queryData"]["source"] == "product":
        return "product"
    return "other"

# generate the sql for my order query, if that is executable
def my_order_sql_query(state: State):
    if "myOrderQuestions" in state:
        user_input = "\n".join(state["myOrderQuestions"])
        user_input = user_input + "\n" + state["question"]
    else:
        user_input = state["question"]

    """Generate SQL query to fetch information."""
    if "customerOrder" in state and state["customerOrder"] is not None:
        custom_prompt = custom_my_one_order_sql_prompt
    else:
        custom_prompt = custom_my_order_sql_prompt
    prompt = custom_prompt.invoke(
        {
            "dialect": db.dialect,
            "table_info": db.get_table_info(["orders"]),
            "input": user_input,
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    sql = result["query"]
    if 'your_customer_id' not in sql.casefold():
        return {"sqlQuery": sql}
    else:
        #logger.info(sql)
        # generated sql missing customer id
        return {"sqlQuery": ''}

# execute the my order sql if a proper one is generated
def execute_my_order_sql_query(state: State):
    sql = state["sqlQuery"]
    if not sql:
        return {"sqlResult": None}
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"sqlResult": execute_query_tool.invoke(state["sqlQuery"])}

# prompt for my order results
def generate_my_order_sql_answer(state: State):
    sql = state["sqlQuery"]
    #logger.info(sql)
    if "myOrderQuestions" in state:
        my_order_questions = state["myOrderQuestions"]
    else:
        my_order_questions = []

    my_order_questions.append(state["question"] + "\n")
    user_input = "\n".join(my_order_questions)

    if not sql:
        prompt = custom_ask_for_id_prompt.invoke({"user_input": user_input})
        #logger.info(prompt)
        # append the short prompt for futher processing
        my_order_questions.append("Your Customer ID? ")
        # generate the answer
        response = llm.invoke(prompt)
        return {"answer": response.content, "myOrderQuestions": my_order_questions}
    else:
        sql_result = state["sqlResult"]
        rows = string_to_list_of_tuples(sql_result)
        if len(rows) == 0:
            prompt = custom_no_data_found_prompt.invoke({"user_input": user_input})
            # generate the answer
            response = llm.invoke(prompt)
            return {"answer": response.content, "myOrderQuestions": [], "customerOrder": None}
        elif len(rows) == 1:
            prompt = custom_order_result_prompt.invoke({"user_input": user_input, "sqlQuery": sql, "sql_result": sql_result})
            # generate the answer
            response = llm.invoke(prompt)
            return {"answer": response.content, "myOrderQuestions": [], "customerOrder": None}
        else:
            prompt = custom_pick_one_order_prompt.invoke(
                {
                    "len_rows": len(rows),
                    "user_input": user_input,
                    "sqlQuery": sql,
                    "sqlResult": state["sqlResult"]
                }
            )
            # append the short prompt for futher processing
            my_order_questions.append("Customer order criteria: ")
            # generate the answer
            response = llm.invoke(prompt)
            return {"answer": response.content, "myOrderQuestions": my_order_questions, "customerOrder": user_input}

# retrieve product info related docs from RAG
def retrieve_product_rags(state: State):
    query = state["queryData"]
    retrieved_docs = vector_store.similarity_search(
        state["question"])
    return {"context": retrieved_docs}

# build prompt from RAGs and return answer
def generate_product_response(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    product_answer = custom_rag_prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(product_answer)
    return {"answer": response.content, "context": []}

# generate order SQL for all orders request
def write_order_sql_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = custom_order_sql_prompt.invoke(
        {
            "dialect": db.dialect,
            "table_info": db.get_table_info(["orders"]),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"sqlQuery": result["query"]}

# execute the all order SQL and store the results
def execute_order_sql_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"sqlResult": execute_query_tool.invoke(state["sqlQuery"])}

# prompt for all order results
def generate_order_sql_answer(state: State):
    prompt = custom_order_sql_response_prompt.invoke(
        {
            "question": state["question"],
            "sqlQuery": state["sqlQuery"],
            "sqlResult": state["sqlResult"]
        }
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

# other topic response
def generate_focused_guide(state: State):
    prompt = custom_other_topic_prompt.invoke(
        {
            "user_input": state["question"]
        }
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

# Build and Compile the graph
graph_builder = StateGraph(State)
graph_builder.add_node("analyze_query", detect_question_type)
graph_builder.add_node("product", retrieve_product_rags)
graph_builder.add_node("generate", generate_product_response)
graph_builder.add_node(product_or_order)
graph_builder.add_node("my_order_or_all_orders", my_order_or_all_orders)
graph_builder.add_node("my orders", my_order_sql_query)
graph_builder.add_node("order", analyze_need_for_customer_id)
graph_builder.add_node("all orders", write_order_sql_query)
graph_builder.add_node(execute_order_sql_query)
graph_builder.add_node(generate_order_sql_answer)
graph_builder.add_node(execute_my_order_sql_query)
graph_builder.add_node(generate_my_order_sql_answer)
graph_builder.add_node("other", generate_focused_guide)

graph_builder.add_edge(START, "analyze_query")
graph_builder.add_conditional_edges("analyze_query", product_or_order)
graph_builder.add_edge("product", "generate")
graph_builder.add_conditional_edges("order", my_order_or_all_orders)
graph_builder.add_edge("all orders", "execute_order_sql_query")
graph_builder.add_edge("execute_order_sql_query", "generate_order_sql_answer")
graph_builder.add_edge("my orders", "execute_my_order_sql_query")
graph_builder.add_edge("execute_my_order_sql_query", "generate_my_order_sql_answer")
graph_builder.add_edge("generate_order_sql_answer", END)
graph_builder.add_edge("generate", END)
graph_builder.add_edge("generate_my_order_sql_answer", END)
graph_builder.add_edge("other", END)

# https://python.langchain.com/docs/how_to/message_history/#example-dictionary-inputs
# https://langchain-ai.github.io/langgraph/how-tos/persistence/#define-graph
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

def respond(question: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    response = graph.invoke({"question": question}, config)
    #logger.info(f'Context: {response["context"]}\n\n')
    if "sqlQuery" in response:
        logger.debug(response["sqlQuery"])
    return response["answer"]
