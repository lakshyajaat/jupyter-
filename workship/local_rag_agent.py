from phi.agent import Agent
from phi.models.ollama import Ollama
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.vectordb.qdrant import Qdrant
from phi.embeddings.ollama import OllamaEmbeddings
from phi.playground import Playground, serve_playground_app
from phi.prompts import PromptTemplate
from phi.memory import ConversationBufferMemory
from phi.chains import RetrievalQA
from phi.tools import Tool
from phi.agents import initialize_agent, AgentType
from phi.config import settingsk

collection_name = "thai-recipe-index"
vector_db = Qdrant(collection_name=collection_name,
                   url="http://localhost:6333/",
                   embedding=OllamaEmbeddings(),
)

knowledge_base = PDFKnowledgeBase(
    urls=["https://phi-ai-public.s3.us-west-2.amazonaws.com/Thai_Recipes.pdf"],
    vector_db=vector_db,
    embedding=OllamaEmbeddings(),
    chunk_size=500,
    chunk_overlap=50,
)

knowledge_base.load(recreate=True, upsert=True)

agent = Agent(
    name="Thai Recipe Agent",
    model=Ollama(id="llama3.2"),
    knowledge_base=knowledge_base,
)

app=Playground(agent=[agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("local_rag_agent:app", reload=True,)
    