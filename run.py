import logging
import argparse

from database import DB, get_sql_db_connection, init_db
from chatbot import respond, init_vectore_store

# Create an ArgumentParser object
parser = argparse.ArgumentParser(description='AI LangChain chatbot sample')

# Add arguments
parser.add_argument('-c', '--create', required = False, help='Create the storage from CVS data', action="store_true")
parser.add_argument('-i', '--interactive', required = False, help='Run in interactive mode', action="store_true")
parser.add_argument('-t', '--test', required = False, help='Run the tests', action="store_true")
args = parser.parse_args()

# generate logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database = DB(get_sql_db_connection, logger)

def test_input(user_input: str, thread_id: str = "test"):
    logger.info(f"User>>> {user_input}")
    answer = respond(user_input, thread_id)
    logger.info(f"Bot>>> {answer}")

def run_tests():
    test_input("What’s a good product for thin guitar strings?")
    test_input("Is the BOYA BYM1 Microphone good for a cello?")
    test_input("What are the top 5 highly-rated guitar products?")
    test_input("Fetch 5 most recent high-priority orders.")
    test_input("What are the details of my last order?")
    test_input("My Customer ID is 77391.")
    test_input("The oldest one.")
    test_input("I want my last order status, my customer id is 37077", "test2")
    test_input("Can I play the piano at Disneys'?", "test2")
    test_input("Ok, fine. What's your best piano?", "test2")

def init_storage():
        init_db(logger)
        init_vectore_store(database)

def interactive_console():
    print("Type one of exit or quit word to stop.")
    while True:
        question = input("Your question? ")
        if question == "quit" or question == "exit":
            break
        answer = respond(question, "console")
        print(f"Bot answer:\n{answer}")
    logger.info("Exiting...")

if __name__ == "__main__":
    if args.create:
        init_storage()
    if args.test:
         run_tests()
    if args.interactive:
         interactive_console()
    