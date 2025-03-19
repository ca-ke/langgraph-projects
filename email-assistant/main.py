from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from router import Router
from prompts import triage_system_prompt, triage_user_prompt


def main():
    prompt_instructions = {
        "triage_rules": {
            "ignore": "Marketing newsletters, spam emails, mass company announcements",
            "notify": "Team member out sick, build system notifications, project status updates",
            "respond": "Direct questions from team members, meeting requests, critical bug reports",
        },
        "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently.",
    }

    profile = {
        "name": "John",
        "full_name": "John Doe",
        "user_profile_background": "Senior software engineer leading a team of 5 developers",
    }
    email = {
        "from": "Alice Smith <alice.smith@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "body": """
            Hi John,

            I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

            Specifically, I'm looking at:
            - /auth/refresh
            - /auth/validate

            Thanks!
            Alice""",
    }
    llm = init_chat_model("deepseek:deepseek-chat")
    llm_router = llm.with_structured_output(Router)

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        examples=None,
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
    )
    user_prompt = triage_user_prompt.format(
        author=email["from"],
        to=email["to"],
        subject=email["subject"],
        email_thread=email["body"],
    )

    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    print(f"Classification: {result.classification}\nReason: {result.reasoning}")


if __name__ == "__main__":
    load_dotenv()
    main()
