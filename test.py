# # import asyncio
# # from abc import ABC, abstractmethod
# # from dataclasses import dataclass, field
# # from typing import Optional, List, Dict

# # # --------------------------
# # # BaseAgent (abstract class)
# # # --------------------------
# # class BaseAgent(ABC):
# #     @abstractmethod
# #     async def run(self, context: "PipelineContext") -> "PipelineContext":
# #         raise NotImplementedError

# #     async def update_trace(self, context: "PipelineContext", agent_name: str, status: str) -> "PipelineContext":
# #         context.trace.append({"agent": agent_name, "status": status})
# #         return context

# # # --------------------------
# # # PipelineContext (dataclass)
# # # --------------------------
# # @dataclass
# # class PipelineContext:
# #     query: str
# #     response: Optional[str] = None
# #     summary: Optional[str] = None
# #     subject: Optional[str] = None
# #     phone: Optional[str] = None
# #     email_status: Optional[str] = None
# #     sms_status: Optional[str] = None
# #     trace: List[dict] = field(default_factory=list)
# #     meta: Dict[str, object] = field(default_factory=dict)

# # # --------------------------
# # # Example Agent
# # # --------------------------
# # class EchoAgent(BaseAgent):
# #     async def run(self, context: PipelineContext) -> PipelineContext:
# #         # Mark as started
# #         context = await self.update_trace(context, "EchoAgent", "started")

# #         # Do some "work" (just echoing back the query)
# #         context.response = f"Echo: {context.query}"

# #         # Mark as done
# #         context = await self.update_trace(context, "EchoAgent", "success")
# #         return context

# # # --------------------------
# # # Run Example
# # # --------------------------
# # async def main():
# #     # Create pipeline context
# #     context = PipelineContext(query="Hello Agent!")

# #     # Create agent
# #     agent = EchoAgent()

# #     # Run agent
# #     updated_context = await agent.run(context)

# #     # Show results
# #     print("Response:", updated_context.response)
# #     print("Trace:", updated_context.trace)

# # asyncio.run(main())




# import asyncio
# from abc import ABC, abstractmethod


# print("=== WITH ABC ===")

# class BaseAgent(ABC):
#     @abstractmethod
#     async def run(self, context):
#         print("run from base")

# # ❌ BadAgent does not implement run
# try:
#     class BadAgent(BaseAgent):
#         print("bad Agent")

#     bad = BadAgent()  # ERROR happens here
# except TypeError as e:
#     print("Error:", e)


# class GoodAgent(BaseAgent):
#     async def run(self, context):
#         return f"Handled: {context}"

# good = GoodAgent()
# print("GoodAgent works:", asyncio.run(good.run("hello")))


# print("\n=== WITHOUT ABC ===")

# class BaseAgentNoABC:
#     @abstractmethod
#     async def run(self, context):
#         print("run from BaseAgentNoABC")

# # ❌ BadAgentNoABC does not implement run
# class BadAgentNoABC(BaseAgentNoABC):
#     pass

# bad2 = BadAgentNoABC()   # ✅ No error yet
# print("BadAgentNoABC instance created successfully")

# # But calling run fails
# try:
#     asyncio.run(bad2.run("hello"))
# except Exception as e:
#     print("Runtime Error:", e)


import redis

# Replace with your actual values
REDIS_HOST = "redis-14714.c90.us-east-1-3.ec2.redns.redis-cloud.com"
REDIS_PORT = 14714
REDIS_PASSWORD = "1v6D0dGsoGqlLcBXXji3ZoxpI4m2TAru"   # find this in your Redis Cloud dashboard

# Connect
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
)

# Test connection
try:
    print("PING:", r.ping())  # Should print True
except Exception as e:
    print("Connection error:", e)

users = {
    "user:1": {"name": "Alice", "age": "25", "education": "Bachelor"},
    "user:2": {"name": "Bob", "age": "30", "education": "Master"},
    "user:3": {"name": "Charlie", "age": "28", "education": "PhD"}
}

# Insert into Redis
for user_id, data in users.items():
    r.hset(user_id, mapping=data)

# Fetch a single user's data
user1 = r.hgetall("user:1")
print({k.decode(): v.decode() for k, v in user1.items()})
# {'name': 'Alice', 'age': '25', 'education': 'Bachelor'}

# Fetch multiple users (names only, for example)
for user_id in users.keys():
    name = r.hget(user_id, "name").decode()
    print(f"{user_id}: {name}")


