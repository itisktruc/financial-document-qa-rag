
import pandas as pd

from data.ground_truth_data import EVALUATION_QUESTIONS
from rag_pipeline import RAGPipeline
from datasets import Dataset
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# RAGAS
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity
)
from datasets import Dataset

EMBEDDING_MODEL = "text-embedding-3-small"
JUDGE_MODEL = "gpt-4o"     # Stronger model for evaluation
evaluation_results = []

# Define metrics to evaluate
metrics = [
    faithfulness,        # Is answer grounded in context?
    answer_relevancy,    # Is answer relevant to question?
    context_precision,   # Are relevant docs ranked higher?
    context_recall,      # Does context have all needed info?
    answer_correctness,  # Is answer factually correct?
    answer_similarity    # Semantic similarity to ground truth
]

def query_rag_for_each_gt():
    for i, item in enumerate(EVALUATION_QUESTIONS, 1):
        print(f"Processing question {i}/{len(EVALUATION_QUESTIONS)}: {item['question'][:50]}...")
    
        # Run RAG
        rag = RAGPipeline()
        result = rag.query(item["question"])
    
        # Add ground truth
        result["ground_truth"] = item["ground_truth"]
    
        evaluation_results.append(result)
        print(f"\n✅ Processed all {len(evaluation_results)} questions")

def prepare_ragas_evaluation_data():
   ragas_data = {
    "question": [r["question"] for r in evaluation_results],
    "answer": [r["answer"] for r in evaluation_results],
    "contexts": [r["contexts"] for r in evaluation_results],
    "ground_truth": [r["ground_truth"] for r in evaluation_results]
    }

    # Create HuggingFace Dataset
   ragas_dataset = Dataset.from_dict(ragas_data)

   print("RAGAS Dataset created")
   print(f"   Columns: {ragas_dataset.column_names}")
   print(f"   Size: {len(ragas_dataset)} samples")
   return ragas_dataset

def run_ragas_evaluation():
    judge_llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)

    query_rag_for_each_gt()
    ragas_dataset = prepare_ragas_evaluation_data()

    results = evaluate(
    dataset=ragas_dataset,
    metrics=metrics,
    llm=judge_llm,
    embeddings=OpenAIEmbeddings(model=EMBEDDING_MODEL))
    print("Evaluation complete!")

    results_df = results.to_pandas()

     # Save results to CSV
    results_df.to_csv("ragas_evaluation_results.csv", index=False)
    print("\nResults saved to 'ragas_evaluation_results.csv'")

    # print("📊 Detailed Results per Question:\n")
    # display_df = results_df[['question', 'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']].copy()
    # display_df['question'] = display_df['question'].str[:50] + '...'
    # display_df

def display_results():
    results_df = pd.read_csv("ragas_evaluation_results.csv")
    print("Detailed Results per Question:\n")
    
    # Select available columns
    available_cols = [col for col in ['question', 'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall'] 
                      if col in results_df.columns]
    
    if not available_cols:
        print("Available columns:", results_df.columns.tolist())
        print(results_df)
        return
    
    display_df = results_df[available_cols].copy()
    if 'question' in display_df.columns:
        display_df['question'] = display_df['question'].astype(str).str[:50] + '...'
    print(display_df)
    
   

if __name__ == "__main__":
    run_ragas_evaluation()
    display_results()
