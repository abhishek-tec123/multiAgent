from AgentProtocol import AgentProtocol

class LoggerAgent(AgentProtocol):
    def __init__(self, filepath="logs.txt"):
        self.filepath = filepath

    async def run(self, context: dict) -> dict:
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write("\n=== NEW AGENT RUN LOG ===\n")
            f.write(f"Query     : {context.get('query', '')}\n")
            f.write(f"Response  : {context.get('response', '')[:300]}...\n")
            f.write(f"Summary   : {context.get('summary', '')}\n")
            f.write(f"Subject   : {context.get('subject', '')}\n")
            f.write(f"Recipient : {context.get('phone', '')}\n")
            f.write(f"Email Sent: {context.get('email_status', 'unknown')}\n")
            f.write(f"SMS Sent  : {context.get('sms_status', 'unknown')}\n")
            f.write("="*40 + "\n")
        print("🗂️ LoggerAgent: Log saved.")
        return context

