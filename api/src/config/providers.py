import os

env = os.environ

# provider: azure_open_ai
#   Cohere-command-r-plus-xrfkk
#   Cohere-command-r-zsfep

# provider: oci
#   cohere.command-r-16k
#   cohere.command-r-plus
#   meta.llama-3-70b-instruct

# provider: azure
#   gpt-4o
#   gpt-4o-mini

# provider: openai
#   gpt-4o
#   gpt-4o-mini


### ALL SENSITIVE DATA MUST BE STORED IN CONNECTION KEY IN THE PROVIDER CONFIGURATION ###
class Config:
    # global defaults
    TEMPERATURE_DEFAULT = 0.0
    TOP_P_DEFAULT = 1.0

    # provider configurations
    AI_PROVIDERS = {
        "azure_ai": {
            "label": "Azure AI",
            "type": "azure_ai",
            "otel_gen_ai_system": "az.ai.inference",
            "connection": {
                "env_prefix": "AZURE_AI_STUDIO_",
                "model": "Cohere-command-r-plus-xrfkk",
                "timeout": 30_000,
            },
            "defaults": {
                "temperature": TEMPERATURE_DEFAULT,
                "top_p": TOP_P_DEFAULT,
                "max_tokens": 2000,
            },
        },
        "groq": {
            "label": "Groq",
            "type": "groq",
            "otel_gen_ai_system": "groq",
            "connection": {
                "api_key": env.get("GROQ_AI_KEY"),
                "endpoint": env.get("GROQ_AI_ENDPOINT"),
            },
            "defaults": {
                "model": env.get("OPENAI_MODEL_DEFAULT"),
                "temperature": TEMPERATURE_DEFAULT,
                "top_p": TOP_P_DEFAULT,
                "max_tokens": 2000,
            },
        },
        "local": {
            "label": "Local",
            "type": "local",
            "otel_gen_ai_system": "local",
            "connection": {
                "api_key": env.get("TMP_LOCAL_OPEN_AI_KEY"),
                "endpoint": env.get("TMP_LOCAL_OPEN_AI_ENDPOINT"),
            },
            "defaults": {
                "temperature": TEMPERATURE_DEFAULT,
                "top_p": TOP_P_DEFAULT,
                "max_tokens": 2000,
            },
        },
        "openai": {
            "label": "OpenAI",
            "type": "openai",
            "otel_gen_ai_system": "openai",
            "connection": {
                "api_key": env.get("OPEN_AI_KEY"),
            },
            "defaults": {
                "model": env.get("OPENAI_MODEL_DEFAULT"),
                "temperature": TEMPERATURE_DEFAULT,
                "top_p": TOP_P_DEFAULT,
                "max_tokens": 2000,
            },
        },
        "azure_open_ai": {
            "label": "Azure Open AI",
            "type": "azure_open_ai",
            "otel_gen_ai_system": "az.ai.openai",
            "connection": {
                "api_key": env.get("AZURE_OPENAI_API_KEY"),
                "endpoint": env.get("AZURE_BASE_URL"),
                "api_version": env.get(
                    "AZURE_OPENAI_API_VERSION", "2023-03-15-preview"
                ),
            },
            "defaults": {
                "model": env.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "temperature": TEMPERATURE_DEFAULT,
                "top_p": TOP_P_DEFAULT,
            },
        },
        "oci": {
            "label": "OCI Cohere",
            "type": "oci",
            "otel_gen_ai_system": "oci",
            "connection": {
                "user": env.get("OCI_USER"),
                "fingerprint": env.get("OCI_FINGERPRINT"),
                "tenancy": env.get("OCI_TENANCY"),
                "region": env.get("OCI_REGION"),
                "key_content": env.get("OCI_KEY"),
                "endpoint": env.get("OCI_ENDPOINT"),
                "compartment_id": env.get("OCI_COMPARTMENT_ID"),
            },
            "defaults": {
                "model": "cohere.command-r-16k",
                "temperature": 1,
                "top_p": 0.75,
                "top_k": 0,
                "max_tokens": 2000,
                "frequency_penalty": 0,
            },
        },
        "oci_llama": {
            "label": "OCI llama",
            "type": "oci_llama",
            "otel_gen_ai_system": "oci",
            "connection": {
                "user": env.get("OCI_USER"),
                "fingerprint": env.get("OCI_FINGERPRINT"),
                "tenancy": env.get("OCI_TENANCY"),
                "region": env.get("OCI_REGION"),
                "key_content": env.get("OCI_KEY"),
                "endpoint": env.get("OCI_ENDPOINT"),
                "compartment_id": env.get("OCI_COMPARTMENT_ID"),
            },
            "defaults": {
                "model": "cohere.command-r-16k",
                "temperature": 1,
                "top_p": 0.75,
                "top_k": -1,
                "max_tokens": 2000,
                "frequency_penalty": 0,
            },
        },
    }
