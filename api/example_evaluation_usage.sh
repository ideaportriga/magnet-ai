#!/bin/bash

# Пример использования новой системы evaluation через scheduler

echo "=== Создание evaluation job через scheduler ==="

# 1. Создание немедленной evaluation задачи для RAG
curl -X POST "http://localhost:8000/evaluation-scheduler/create-evaluation-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RAG Tool Performance Test",
    "evaluation_type": "rag_eval",
    "iteration_count": 2,
    "config": [
      {
        "system_name": "my_rag_tool",
        "test_set_system_names": ["customer_support_questions", "product_questions"],
        "variants": ["default", "optimized"]
      }
    ],
    "result_entity": "evaluations"
  }'

echo -e "\n\n=== Создание evaluation job для Prompt Template ==="

# 2. Создание evaluation для Prompt Template
curl -X POST "http://localhost:8000/evaluation-scheduler/create-evaluation-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prompt Template A/B Test",
    "evaluation_type": "prompt_eval",
    "iteration_count": 1,
    "config": [
      {
        "system_name": "customer_response_template",
        "test_set_system_names": ["customer_interactions_test"],
        "variants": ["formal", "friendly", "concise"]
      }
    ],
    "result_entity": "evaluations"
  }'

echo -e "\n\n=== Создание задачи через общий scheduler endpoint ==="

# 3. Альтернативный способ через общий scheduler endpoint
curl -X POST "http://localhost:8000/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily RAG Evaluation",
    "job_type": "recurring",
    "cron": {
      "hour": "2",
      "minute": "0"
    },
    "run_configuration": {
      "type": "evaluation",
      "params": {
        "type": "rag_eval",
        "iteration_count": 1,
        "config": [
          {
            "system_name": "production_rag_tool",
            "test_set_system_names": ["production_test_set"],
            "variants": ["current"]
          }
        ],
        "result_entity": "evaluations"
      }
    }
  }'

echo -e "\n\n=== Проверка статуса задач ==="

# 4. Проверка статуса scheduler
curl -X GET "http://localhost:8000/scheduler/pool-status"

echo -e "\n\nГотово! Все evaluation задачи созданы."
