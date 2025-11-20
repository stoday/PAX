import termlit
from clockmate.llm_cli import main as clockmate_main

termlit.welcome(
    title="Welcome~",
    subtitle="version 1.0.0",
    description="This is a note",
)

while True:
    prompt = termlit.input("需要我協助您打卡嗎(y/n): ")

    if prompt.lower() in {"no", "n"}:
        termlit.goodbye("再見！期待下次")
        break
    if prompt.lower() in {"yes", "y"}:
        clockmate_main()
        break
    with termlit.spinner("dots", "正在處理您的問題..."):
        response = termlit.post(
            url="https://httpbin.org/post",
            json={"question": prompt},
            log=False,
        )
        
    termlit.write('回答: ' + str(response.json()))
    