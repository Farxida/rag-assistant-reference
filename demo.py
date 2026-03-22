import sys
from src.retrieval.rag import RAGPipeline

def main():
    if len(sys.argv) < 2:
        print('Usage: python demo.py "your question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    rag = RAGPipeline()
    result = rag.query(question, verbose=True)

    print(f"\nQ: {question}")
    print(f"\nA: {result['answer']}")
    print(f"\nSources: {', '.join(result['sources'])}")

if __name__ == "__main__":
    main()
