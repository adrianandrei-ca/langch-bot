Welcome a demo implementation of a eCommerce chat bot using langchain.

It implements a multi-source stateful solution that uses RAG and SQL tables to create responses.

There are two data sources:
- musical related products
- customer orders, each bearing a customer id.

The solution is stateful, in the sense that when an incomplete question is asked the bot is asking for missing data and then performs to generate the proper response.

Example:
<code>
User>>> What are the details of my last order?
Bot>>> Please provide your Customer ID to retrieve the details of your last order.
User>>> My Customer ID is 77391.
Bot>>> You have two orders associated with your Customer ID 77391: one placed on 2018-10-26 and another on 2018-09-28. Which order would you like to inquire about?
User>>> The oldest one.
Bot>>> Your order for one pair of Sneakers placed on 2018-09-28 at 14:29:32 has a shipping cost of $6.2 and the total sales amount was $62. Let me know if you'd like more details or need assistance with this order!

</code>

The solution identifies the data source based on context using Pydentic approach, so the question below is responded from the product table using RAG.
<code>
User>>> What are the top 5 highly-rated guitar products?
Bot>>> The top 5 highly-rated guitar products based on the provided context are:

1. WINGO Guitar Capo for Acoustic and Electric Guitars - Known for its quick release and versatile compatibility with various string instruments.
2. Amazon Basics Adjustable Guitar Folding A-Frame Stand - Features a lightweight design with non-slip rubber and soft foam arms for protection.
3. D'Addario XL Nickel Electric Guitar Strings - Renowned for their bright tone and reliable durability, popular among musicians since 1974.
4. Ernie Ball Mondo Slinky Nickelwound Electric Guitar Strings - Favored by professional musicians for their balanced tone and heavy gauge.
5. D'Addario XL Nickel Electric Guitar Strings in High-Strung/Nashville Tuning - Offers a unique shimmering tone suitable for various musical styles.

Would you like more details on any of these products or suggestions for other options?

</code>

**Environment Variables Setup**

Setup a shell file (env_setup.sh for instance) and add the following variables:
<code>
export OPENAI_API_KEY=sk-...

#add those if you want to use langraph to trace the graph execution
export LANGCHAIN_API_KEY="lsv2_..."
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
export LANGCHAIN_PROJECT="pr-..."
</code>

Execute this file before running <code>run.py</code>, for example in Linux one can do:
<code>
. ../env_setup.sh
</code>

**Run Setup**

Create your Python environment (I use version 3.12) and install the dependencies:
<code>
pip install -r requirements.txt
</code>

**Initial Configuration - Creating the storage from the CSV files**

The raw data files for orders and products are in the data folder. They will be imported in the SQL database as well as the vector store.
<code>
python run.py -c
</code>

That will add over 50000 products into the vector store.

**Running the test cases**

There are 10 tests build in, to illustrate the bot capabilities. You can use some of them as template for the interactive mode.
<code>
python run.py -t
</code>

**Running the interactive mode**

You can use custom questions by running in the interactive mode:
<code>
python run.py -i
</code>
To exit the interactive mode, type <code>exit</code> or <code>quit</code>

**Code Description and Tweaks**

The <code>run.py</code> file contains the top level code to setup and run the bot based on run arguments. The two subsequent folders deal with the database setup and API (<code>database</code>) and with the LangChain bot implementation (<code>chatbot</code>).
In it, <code>chat.py</code> has the vector storage code, then the prompt templates, the node implementation and finally the graph build. The bot state is implemented throughout the nodes which makes the solution less elegant tham originally hoped. I would have loved LangChain to have a contextual approach in the graph implementation so depedent responses reflect implicitly in the state, but this is another topic.

The RAG retrieval is not done through an agent tool approach but rather through a node. The implementation can be changed for that to eventually combine a SQL + RAG approach on product questions later on.

If you do not want all the products stored in the embedding vector one can change the <code>facade.py/products_as_documents</code> method and add <code>LIMIT 100</code> on the select statement to minimize time and cost.
