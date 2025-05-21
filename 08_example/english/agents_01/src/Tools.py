from typing import Optional
import os
import time
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from .Memory import MemoryClass
from .Storage import get_user
from langchain_core.output_parsers import PydanticOutputParser

# 配置管理
class Config:
    def __init__(self):
        load_dotenv()
        self.setup_environment()
        
    @staticmethod
    def setup_environment():
        required_vars = [
            "SERPAPI_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_API_BASE",
            "DINGDING_ID",
            "DINGDING_SECRET",
            "DINGDING_UNION_ID"
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                raise EnvironmentError(f"Missing required environment variable: {var}")
            
        os.environ.update({
            "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE")
        })

# DingTalk API 客户端
class DingTalkClient:
    def __init__(self):
        self.app_key = os.getenv("DINGDING_ID")
        self.app_secret = os.getenv("DINGDING_SECRET")
        self.union_id = os.getenv("DINGDING_UNION_ID")
        
    def get_access_token(self) -> str:
        if not all([self.app_key, self.app_secret, self.union_id]):
            raise ValueError("钉钉配置信息不完整")
            
        try:
            response = requests.post(
                "https://api.dingtalk.com/v1.0/oauth2/accessToken",
                json={"appKey": self.app_key, "appSecret": self.app_secret}
            )
            response.raise_for_status()
            token = response.json().get("accessToken")
            if not token:
                raise ValueError("获取钉钉访问令牌失败")
            return token
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"获取访问令牌失败: {str(e)}")

# 保持原有的 Pydantic 模型定义
class TodoInput(BaseModel):
    subject: str = Field(description="待办事项标题")
    dueTime: int = Field(None, description="截止时间，Unix时间戳，单位毫秒，例如1617675000000,当前时间为{}".format(int(time.time() * 1000)))
    description: str = Field(None, description="待办事项描述")
    priority: int = Field(0, description="优先级 10：较低 20：普通 30：紧急 40：非常紧急")

class ScheduleSchema(BaseModel):
    userIds: str = Field(description=f"用户ID")
    startTime: str = Field(None, description="查询开始时间，格式必须为:2020-01-01T10:15:30+08:00,当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))
    endTime: str = Field(None, description="查询结束时间，格式必须为:2020-01-01T10:15:30+08:00,当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))

class ScheduleSchemaSet_data(BaseModel):
    date: str = Field(description=f"日程开始日期，格式：yyyy-MM-dd,当前时间为{time.strftime('%Y-%m-%d')},说明(全天日程必须有值,非全天日程必须留空)")
    dateTime: str = Field(description=f"日程开始时间，格式为ISO-8601的date-time格式{time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())},说明(全天日程必须留空,非全天日程必须有值)")
    timeZone: str = Field(description=f"日程开始时间所属时区，TZ database name格式,固定为Asia/Shanghai,说明(全天日程必须留空,非全天日程必须有值)")

class ScheduleSchemaSet_data_end(BaseModel):
    date: str = Field(description=f"日程结束日期，格式：yyyy-MM-dd,当前时间为{time.strftime('%Y-%m-%d')},说明（全天日程：必须有值结束时间需传 T+1例如 2024-06-01 的全天日程，开始时间为 2024-06-01，则结束时间应该写 2024-06-02。非全天日程必须留空")
    dateTime: str = Field(description=f"日日程结束时间，格式为ISO-8601的date-time格式，当前时间为{time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())}，说明（全天日程必须留空，非全天日程必须有值）")
    timeZone: str = Field(description=f"日程结束时间所属时区，必须和开始时间所属时区相同，TZ database name格式,固定为Asia/Shanghai，说明（全天日程必须留空非全天日程必须有值")

class ScheduleSchemaSet(BaseModel):
    summary: str = Field(description=f"日程标题，最大不超过2048个字符")
    start: ScheduleSchemaSet_data = Field(description="日程开始时间")
    end: ScheduleSchemaSet_data_end = Field(description="日程结束时间")
    isAllDay: bool = Field(description="是否全天日程。true：是false：不是")
    description: str = Field(description=f"日程描述，最大不超过5000个字符")

class ScheduleSearch(BaseModel):
    timeMin: Optional[str] = Field(None, description="日程开始时间的最小值，格式为ISO-8601的date-time格式，可不填,说明(timeMin和 timeMax最大差值为一年),当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))
    timeMax: Optional[str] = Field(None, description="日程开始时间的最大值，格式为ISO-8601的date-time格式，可不填,说明(timeMin和 timeMax最大差值为一年),当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))

class ScheduleModify(BaseModel):
    timeMin: Optional[str] = Field(None, description="日程开始时间的最小值，格式为ISO-8601的date-time格式，可不填,说明(timeMin和 timeMax最大差值为一年),当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))
    timeMax: Optional[str] = Field(None, description="日程开始时间的最大值，格式为ISO-8601的date-time格式，可不填,说明(timeMin和 timeMax最大差值为一年),当前时间为{}".format(time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())))
    description: Optional[str] = Field(None, description=f"日程描述，最大不超过5000个字符")
    start: Optional[ScheduleSchemaSet_data] = Field(None, description="日程开始时间")
    end: Optional[ScheduleSchemaSet_data_end] = Field(None, description="日程结束时间")
    summary: Optional[str] = Field(None, description=f"日程标题，最大不超过2048个字符")

# 删除模型
class DeleteSchedule(BaseModel):
    summary: str = Field(description="日程标题")
    description: Optional[str] = Field(description="日程描述")



class EventsId(BaseModel):
    id: str = Field(description="日程id")
    isAllDay: bool = Field(description="是否全天日程")

class ScheduleDel(BaseModel):
    eventid: str = Field(description="日程id")

# 工具函数
@tool
def search(query: str) -> str:
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具."""
    serp = SerpAPIWrapper()
    return serp.run(query)

@tool(parse_docstring=True)
def get_info_from_local(query: str) -> str:
    """从本地知识库获取信息。

    Args:
        query (str): 用户的查询问题

    Returns:
        str: 从知识库中检索到的答案
    """
    print("-------RAG-------------")
    userid = get_user("userid")
    print(userid)
    llm = ChatOpenAI(model=os.getenv("BASE_MODEL"))
    memory = MemoryClass(memorykey=os.getenv("MEMORY_KEY"),model=os.getenv("BASE_MODEL"))
    chat_history = memory.get_memory(session_id=userid).messages if userid else []
    
    condense_question_prompt = ChatPromptTemplate.from_messages([
        ("system", "给出聊天记录和最新的用户问题。可能会引用聊天记录中的上下文，提出一个可以理解的独立问题。没有聊天记录，请勿回答。必要时重新配制，否则原样退还。"),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    client = QdrantClient(path=os.getenv("PERSIST_DIR","./vector_store"))
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name=os.getenv("EMBEDDING_COLLECTION"), 
        embedding=OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "Pro/BAAI/bge-m3"),
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_API_BASE")
        )
    )
    
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 10}
    )
    
    qa_chain = create_retrieval_chain(
        create_history_aware_retriever(llm, retriever, condense_question_prompt),
        create_stuff_documents_chain(
            llm,
            ChatPromptTemplate.from_messages([
                ("system", "你是回答问题的助手。使用下列检索到的上下文回答。这个问题。如果你不知道答案，就说你不知道。最多使用三句话，并保持回答简明扼要。\n\n{context}"),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])
        )
    )
    
    res = qa_chain.invoke({
        "input": query,
        "chat_history": chat_history,
    })
    print("-------RAG- OUTPUT------------")
    print(res)
    return res["answer"]

@tool
def create_todo(todo: TodoInput) -> str:
    """创建一个待办事项
    Args:
        todo: 包含待办事项信息的对象
    Returns:
        str: 创建结果消息
    """
    client = DingTalkClient()
    token = client.get_access_token()
    
    todo_data = {
        "subject": todo.subject,
        "notifyConfigs": {"dingNotify": "1"}
    }
    
    if todo.dueTime:
        todo_data["dueTime"] = todo.dueTime
    if todo.description:
        todo_data["description"] = todo.description
    if todo.priority:
        todo_data["priority"] = todo.priority
        
    try:
        response = requests.post(
            f"https://api.dingtalk.com/v1.0/todo/users/{client.union_id}/tasks",
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            },
            json=todo_data
        )
        response.raise_for_status()
        return f"成功创建待办事项: {todo.subject}"
    except requests.exceptions.RequestException as e:
        return f"创建待办事项失败: {str(e)}"

@tool
def checkSchedule(schedule: ScheduleSchema) -> str:
    """检查用户在某段时间内的忙闲状态
    Args:
        schedule: 包含查询时间范围的对象
    Returns:
        str: 查询结果消息
    """
    client = DingTalkClient()
    token = client.get_access_token()
    
    try:
        response = requests.post(
            f"https://api.dingtalk.com/v1.0/calendar/users/{client.union_id}/querySchedule",
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            },
            json={
                "userIds": [client.union_id],
                "startTime": schedule.startTime,
                "endTime": schedule.endTime
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"查询日程失败: {str(e)}"

@tool
def SetSchedule(sets: ScheduleSchemaSet) -> str:
    """创建日程
    Args:
        sets: 包含日程信息的对象
    Returns:
        str: 创建结果消息
    """
    client = DingTalkClient()
    token = client.get_access_token()

    # 在创建之前先检查忙闲状态
    # Extract time info from sets parameter to check availability
    schedule_schema = ScheduleSchema(
        userIds=client.union_id,
        startTime=sets.start.dateTime if not sets.isAllDay else f"{sets.start.date}T00:00:00+08:00",
        endTime=sets.end.dateTime if not sets.isAllDay else f"{sets.end.date}T00:00:00+08:00"
    )
    schedule_dict = {
        "schedule": schedule_schema.model_dump()
    }
    # Check if the time slot is available
    availability = checkSchedule.invoke(schedule_dict)
    
    if availability and "scheduleInformation" in availability:
        schedule_items = availability["scheduleInformation"][0].get("scheduleItems", [])
        input_start = sets.start.dateTime if not sets.isAllDay else f"{sets.start.date}T00:00:00+08:00"
        input_end = sets.end.dateTime if not sets.isAllDay else f"{sets.end.date}T00:00:00+08:00"
        
        for item in schedule_items:
            item_start = item["start"]["dateTime"]
            item_end = item["end"]["dateTime"]
            
            # Check for time overlap
            if (item_start <= input_end and item_end >= input_start):
                if item["status"] == "BUSY":
                    return "该时间段已有其他日程安排且状态为忙碌，请选择其他时间"
    
    request_data = {
        "summary": sets.summary,
        "description": sets.description,
        "isAllDay": sets.isAllDay,
    }

    if sets.isAllDay:
        request_data["start"] = {"date": sets.start.date}
        request_data["end"] = {"date": sets.end.date}
    else:
        request_data["start"] = {
            "dateTime": sets.start.dateTime,
            "timeZone": sets.start.timeZone
        }
        request_data["end"] = {
            "dateTime": sets.end.dateTime,
            "timeZone": sets.end.timeZone
        }

    try:
        response = requests.post(
            f"https://api.dingtalk.com/v1.0/calendar/users/{client.union_id}/calendars/primary/events",
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            },
            json=request_data
        )
        response.raise_for_status()
        return f"成功创建日程: {sets.summary}"
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e.response, 'text'):
            error_message += f"\nResponse: {e.response.text}"
        print(f"Error details: {error_message}")
        return f"创建日程失败: {error_message}"

@tool
def SearchSchedule(search: ScheduleSearch) -> str:
    """查询日程
    Args:
        search: 包含查询时间范围的对象
    Returns:
        str: 查询结果消息
    """
    client = DingTalkClient()
    token = client.get_access_token()
    
    try:
        response = requests.get(
            f"https://api.dingtalk.com/v1.0/calendar/users/{client.union_id}/calendars/primary/events",
            params={
                "timeMin": search.timeMin,
                "timeMax": search.timeMax
            },
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"查询日程失败: {str(e)}"

def FindPreciseOrder(orginrder: str,events:object) -> str:
    """查找精确的指令"""
    llm = ChatOpenAI(model=os.getenv("BASE_MODEL"))
    prompt = ChatPromptTemplate.from_messages([
        ("system", """请根据用户的输入和查询到的日程信息，提取出与用户输入最匹配的1个日程id以及是否为全天事件。注意查询到的数据结构为：{{'events':[{{
            'attendees': [],
            'categories': [],
            'createTime': '2023-09-26T08: 24: 18Z',
            'description': '',
            'end': '',
            'extendedProperties': '',
            'id': '',
            'isAllDay': False,
            'organizer': '',
            'reminders': [
            ],
            'start': '',
            'status': '',
            'summary': 'xxxxxx,
            'updateTime': ''
        }}]}} 日程id为events中的id字段，例如events[0]['id']，是否为全天事件字段为events中的isAllDay，例如events[0]['isAllDay']，有可能存在多个events项，你需要根据用户输入来匹配筛选，输出结构化数据,不要有其他输出。查询到的日程信息为：{events}"""),
        ("human", "{input}"),
    ])
    try:
        parser = PydanticOutputParser(pydantic_object=EventsId)
        prompt.partial_variables = {"format_instructions": parser.get_format_instructions()}
        chain = prompt | llm | parser
        return chain.invoke({"input": orginrder,"events":events})
    except Exception as e:
        print(e)
        return None



@tool
def ModifySchedule(search: ScheduleModify) -> str:
    """修改日程
    Args:
        search: 包含查询时间范围的对象
    Returns:
        str: 修改结果消息
    """
    # 创建 ScheduleSearch 对象并转换为字典
    search_params = ScheduleSearch(
        timeMin=search.timeMin,
        timeMax=search.timeMax
    )
    
    # 包装成正确的格式：添加 search 字段
    search_dict = {
        "search": search_params.model_dump()
    }
    
    # 使用 invoke 方法调用 SearchSchedule
    searchResult = SearchSchedule.invoke(search_dict)
    if isinstance(searchResult, str):
        return "查询日程失败"
        
    events = searchResult.get('events', [])
    print(events)
    if not events:
        return "您的日程空空如也"
    if len(events) > 1:
        orginOder = f"description: {search.description}, start: {search.start}, end: {search.end}, summary: {search.summary}"
        returnID = FindPreciseOrder(orginOder,events)
        print(returnID)
        eventid = returnID.id
        isAllDay = returnID.id
        if not eventid:
            return "您的日程似乎不存在，是否输入有误？"
    else:
        eventid = events[0]['id']
        isAllDay = events[0]['isAllDay']
    # 获取钉钉 API 客户端
    client = DingTalkClient()
    token = client.get_access_token()
    print(eventid)
    print(token)
    try:
        request_data = {
            "id":eventid
        }
        if search.summary:
            request_data["summary"] = search.summary
        if search.description:
            request_data["description"] = search.description
        if search.start:
            if isAllDay:
                request_data["start"] = {
                    "date": search.start.date,
                    "dateTime": search.start.dateTime,
                    "timeZone": search.start.timeZone
                }
            else:
                request_data["start"] = {
                    "dateTime": search.start.dateTime,
                    "timeZone": search.start.timeZone
                }
                

        if search.end:
            if isAllDay:
                request_data["end"] = {
                    "date": search.end.date,
                    "dateTime": search.end.dateTime,
                    "timeZone": search.end.timeZone
                }
            else:
                request_data["end"] = {
                    "dateTime": search.end.dateTime,
                    "timeZone": search.end.timeZone
                }

        print("提交数据：")
        print(request_data)
        response = requests.put(
            f"https://api.dingtalk.com/v1.0/calendar/users/{client.union_id}/calendars/primary/events/{eventid}",
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            },
            json=request_data
        )
        response.raise_for_status()
        return f"成功修改日程"
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e.response, 'text'):
            error_message += f"\nResponse: {e.response.text}"
        print(f"Error details: {error_message}")
        return f"创建日程失败: {error_message}"
@tool
def DelSchedule(query: DeleteSchedule) -> str:
    """当用户要求删除日程时调用此工具
    Args:
        query: 用户要删除的日程信息
    Returns:
        str: 返回给用户确认要具体删除的日程信息
    """
    # 创建 ScheduleSearch 对象并转换为字典
    search_params = ScheduleSearch()
    # 包装成正确的格式：添加 search 字段
    search_dict = {
        "search": search_params.model_dump()
    }
    # 使用 invoke 方法调用 SearchSchedule
    searchResult = SearchSchedule.invoke(search_dict)
    events = searchResult.get('events', [])
    if not events:
        return "您的日程空空如也"
    if len(events) > 1:
        orginOder = f"description: {query.description}, summary: {query.summary}"
        returnID = FindPreciseOrder(orginOder,events)
        print(returnID)
        eventid = returnID.id
        if not eventid:
            return "您的日程似乎不存在，是否输入有误？"
    else:
        eventid = events[0]['id']
    print("要删除的日程ID：",eventid)
    return f"记录下日程id,然后询问用户，是否确认要删除日程 {eventid}"

@tool
def ConfirmDelSchedule(query: ScheduleDel) -> str:
    """当用户确认删除日程信息时调用此工具
    Args:
        query: 用户要删除的日程id"
    Returns:
        str: 返回给用户删除日程的结果
    """
    print("要删除的日程ID：",query.eventid)
    # 获取钉钉 API 客户端
    client = DingTalkClient()
    token = client.get_access_token()
    try:
        response = requests.delete(
            f"https://api.dingtalk.com/v1.0/calendar/users/{client.union_id}/calendars/primary/events/{query.eventid}?pushNotification=true",
            headers={
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            }
        )
        response.raise_for_status()
        return f"成功删除日程"
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e.response, 'text'):
            error_message += f"\nResponse: {e.response.text}"
        print(f"Error details: {error_message}")
        return f"删除日程失败: {error_message}"
        


# 初始化配置
Config()
