import sys
import uuid
from orchestrator.pipeline import run_pipeline

def main():
    try:
        user_query = input('Enter your question: ')
        if not user_query:
            print('No question entered. Exiting.')
            return
        request_id = str(uuid.uuid4())
        run_pipeline(user_query, request_id=request_id)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit(0)
    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)
if __name__ == '__main__':
    main()