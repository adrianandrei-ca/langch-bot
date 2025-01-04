Welcome a demo implementation of a eCommerce chat bot using langchain.

It implements a multi-source stateful solution that uses RAG and SQL tables to create responses.

**Environment Variables**

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

**Installation**

Create your Python environment (I use version 3.12) and install the dependencies:
<code>
pip install -r requirements.txt
</code>

**Creating the storage from the CSV files**

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
