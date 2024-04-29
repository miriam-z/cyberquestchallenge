from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_anthropic import ChatAnthropic
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.docstore.document import Document


import chainlit as cl
from chainlit.types import AskFileResponse


# RESUME LOGIC
from operator import itemgetter

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from chainlit.types import ThreadDict
# RESUME LOGIC


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

welcome_message = """Welcome to the CyberQuest Challenge: A PDF QA demo! To get started:
1. Upload a PDF file
2. Ask a question about the file
"""


def process_file(file: AskFileResponse):
    Loader = PyPDFLoader

    if file is None or not file.path:
        return None
    
    try:
        loader = Loader(file.path)
        documents = loader.load()
        docs = text_splitter.split_documents(documents)
        for i, doc in enumerate(docs):
            doc.metadata["source"] = f"source_{i}"
        return docs
    except Exception as e:
        print(f"Error processing file: {e}")
        return None


def get_docsearch(file: AskFileResponse):
    docs = process_file(file)

    if docs is None:
        return None
    
    # save data in the user session
    cl.user_session.set("docs", docs)

    docsearch = Chroma.from_documents(documents=docs, embedding=embeddings)

    return docsearch


@cl.on_chat_start
async def start():
    
    # Resume Logic
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    setup_runnable()
    # Resume Logic
    
    await cl.Avatar(
        name="CyberQuest Challenge",
        url="https://avatars.githubusercontent.com/u/128686189?s=400&u=a1d1553023f8ea0921fba0debbe92a8c5f840dd9&v=4",
    ).send()
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content=welcome_message,
            accept=["application/pdf"],
            max_size_mb=20,
            timeout=180,
        ).send()

    file = files[0]

    msg = cl.Message(
        content=f"Processing `{file.name}`...", disable_feedback=True)
    await msg.send()

    docsearch = await cl.make_async(get_docsearch)(file)

    message_history = ChatMessageHistory()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    chain = ConversationalRetrievalChain.from_llm(
        ChatAnthropic(
            model='claude-3-opus-20240229',
            temperature=0, 
            streaming=True, ),
        #     system=f"You are an expert research assistant. Here is a document you will answer questions about:\n<doc>\n{file.name}\n</doc>\n\nFirst, find the quotes from the document that are most relevant to answering the question, and then print them in numbered order. Quotes should be relatively short.\n\nIf there are no relevant quotes, write \"No relevant quotes\" instead.\n\nThen, answer the question, starting with \"Answer:\". Do not include or reference quoted content verbatim in the answer. Don't say \"According to Quote [1]\" when answering. Instead make references to quotes relevant to each section of the answer solely by adding their bracketed numbers at the end of relevant sentences.\n\nThus, the format of your overall response should look like what's shown between the <example></example> tags. Make sure to follow the formatting and spacing exactly.",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": [
        #                 {
        #                     "type": "text",
        #                     "text": msg.content
        #                 }
        #             ]
        #         }
        #     ]
        # ),
        chain_type="stuff",
        retriever=docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 6}),
        memory=memory,
        return_source_documents=True,
    )

    # let the user know that the system is ready
    msg.content = f"`{file.name}` processed. You can now ask questions!"
    await msg.update()

    cl.user_session.set("chain", chain)
    cl.user_session.set("message_history", message_history)


@cl.on_message
async def main(message: cl.Message):
    
    # RESUME LOGIC
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory

    runnable = cl.user_session.get("runnable")  # type: Runnable

    res = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)
    # RESUME LOGIC
    
    chain = cl.user_session.get("chain")  # type: ConversationalRetrievalChain
    cb = cl.AsyncLangchainCallbackHandler()
    res = await chain.acall(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents = res["source_documents"]  # type: List[Document]

    text_elements = []  # type: List[cl.Text]

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            # create the text element referenced in the message
            text_elements.append(
                cl.Text(content=source_doc.page_content, name=source_name)
            )
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"

    await cl.Message(content=answer, elements=text_elements).send()
    
    
# Add Resume-Chat Functionality    
def setup_runnable():
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)

    
@cl.password_auth_callback
def auth():
    return cl.User(identifier="test")


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] == None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()    