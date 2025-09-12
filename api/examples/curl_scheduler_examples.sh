#!/bin/bash

# Примеры вызова существующего endpoint /scheduler/create-job для evaluation

echo "=== Примеры использования /scheduler/create-job для Evaluation ==="
echo ""

# Функция для красивого вывода JSON
pretty_print() {
    if command -v jq &> /dev/null; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

BASE_URL="http://localhost:8000"

echo "🚀 Пример 1: Немедленная RAG evaluation"
echo "curl -X POST $BASE_URL/scheduler/create-job"
echo ""

response=$(curl -s -X POST "$BASE_URL/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RAG Tool Performance Test",
    "job_type": "one_time_immediate",
    "run_configuration": {
      "type": "evaluation",
      "params": {
        "type": "rag_eval",
        "iteration_count": 3,
        "config": [
          {
            "system_name": "customer_support_rag",
            "test_set_system_names": ["support_questions_v1", "support_questions_v2"],
            "variants": ["default", "optimized"]
          }
        ],
        "result_entity": "evaluations"
      }
    },
    "job_id": null,
    "interval": null,
    "notification_email": null,
    "cron": null,
    "scheduled_start_time": null,
    "status": null,
    "timezone": null
  }')

echo "Ответ:"
pretty_print "$response"
echo ""
echo "==========================================================================================================="
echo ""

echo "🧪 Пример 2: Prompt Template evaluation"
echo "curl -X POST $BASE_URL/scheduler/create-job"
echo ""

response=$(curl -s -X POST "$BASE_URL/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prompt Template A/B Test",
    "job_type": "one_time_immediate",
    "run_configuration": {
      "type": "evaluation",
      "params": {
        "type": "prompt_eval",
        "iteration_count": 2,
        "config": [
          {
            "system_name": "customer_response_template",
            "test_set_system_names": ["customer_interactions"],
            "variants": ["formal", "friendly", "concise"]
          }
        ],
        "result_entity": "evaluations"
      }
    },
    "job_id": null,
    "interval": null,
    "notification_email": null,
    "cron": null,
    "scheduled_start_time": null,
    "status": null,
    "timezone": null
  }')

echo "Ответ:"
pretty_print "$response"
echo ""
echo "==========================================================================================================="
echo ""

echo "📅 Пример 3: Запланированная evaluation (завтра в 14:00)"
echo "curl -X POST $BASE_URL/scheduler/create-job"
echo ""

# Вычисляем дату завтра в 14:00
TOMORROW_2PM=$(date -d "tomorrow 14:00" -Iseconds 2>/dev/null || date -v+1d -v14H -v0M -v0S "+%Y-%m-%dT%H:%M:%S")

response=$(curl -s -X POST "$BASE_URL/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Scheduled RAG Evaluation\",
    \"job_type\": \"one_time_scheduled\",
    \"scheduled_start_time\": \"$TOMORROW_2PM\",
    \"run_configuration\": {
      \"type\": \"evaluation\",
      \"params\": {
        \"type\": \"rag_eval\",
        \"iteration_count\": 1,
        \"config\": [
          {
            \"system_name\": \"production_rag_tool\",
            \"test_set_system_names\": [\"production_test_set\"],
            \"variants\": [\"current\"]
          }
        ],
        \"result_entity\": \"evaluations\"
      }
    },
    \"job_id\": null,
    \"interval\": null,
    \"notification_email\": null,
    \"cron\": null,
    \"status\": null,
    \"timezone\": null
  }")

echo "Запланировано на: $TOMORROW_2PM"
echo "Ответ:"
pretty_print "$response"
echo ""
echo "==========================================================================================================="
echo ""

echo "🔄 Пример 4: Повторяющаяся evaluation (каждый день в 2:00)"
echo "curl -X POST $BASE_URL/scheduler/create-job"
echo ""

response=$(curl -s -X POST "$BASE_URL/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Production RAG Evaluation",
    "job_type": "recurring",
    "cron": {
      "hour": 2,
      "minute": 0,
      "second": 0,
      "year": null,
      "month": null,
      "day": null,
      "week": null,
      "day_of_week": null,
      "start_date": null,
      "end_date": null,
      "jitter": null
    },
    "scheduled_start_time": null,
    "run_configuration": {
      "type": "evaluation",
      "params": {
        "type": "rag_eval",
        "iteration_count": 1,
        "config": [
          {
            "system_name": "production_rag_tool",
            "test_set_system_names": ["daily_test_set"],
            "variants": ["production"]
          }
        ],
        "result_entity": "evaluations"
      }
    },
    "job_id": null,
    "interval": null,
    "notification_email": null,
    "status": null,
    "timezone": "UTC"
  }')

echo "Ответ:"
pretty_print "$response"
echo ""
echo "==========================================================================================================="
echo ""

echo "📊 Пример 5: Еженедельная evaluation (понедельники в 9:00)"
echo "curl -X POST $BASE_URL/scheduler/create-job"
echo ""

response=$(curl -s -X POST "$BASE_URL/scheduler/create-job" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly RAG Performance Report",
    "job_type": "recurring",
    "cron": {
      "day_of_week": "monday",
      "hour": 9,
      "minute": 0,
      "second": 0,
      "year": null,
      "month": null,
      "day": null,
      "week": null,
      "start_date": null,
      "end_date": null,
      "jitter": null
    },
    "scheduled_start_time": null,
    "run_configuration": {
      "type": "evaluation",
      "params": {
        "type": "rag_eval",
        "iteration_count": 5,
        "config": [
          {
            "system_name": "main_rag_tool",
            "test_set_system_names": ["comprehensive_test_set"],
            "variants": ["production", "staging"]
          }
        ],
        "result_entity": "evaluations"
      }
    },
    "job_id": null,
    "interval": null,
    "notification_email": "admin@company.com",
    "status": null,
    "timezone": "UTC"
  }')

echo "Ответ:"
pretty_print "$response"
echo ""
echo "==========================================================================================================="
echo ""

echo "📊 Проверка статуса scheduler"
echo "curl -X GET $BASE_URL/scheduler/pool-status"
echo ""

status_response=$(curl -s -X GET "$BASE_URL/scheduler/pool-status")
echo "Ответ:"
pretty_print "$status_response"
echo ""

echo "✅ Все примеры выполнены!"
echo ""
echo "Для отмены задачи используйте:"
echo "curl -X POST $BASE_URL/scheduler/cancel-job -H 'Content-Type: application/json' -d '{\"job_id\": \"your-job-id\"}'"
