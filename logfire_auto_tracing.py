import logfire
import uvicorn
from decouple import config


logfire.configure(
    token=config("LOGFIRE_SIXSIGMA"),
    code_source=logfire.CodeSource(
        repository="https://github.com/EvgenyMeredelin/six-sigma",
        revision="main"
    )
)
logfire.install_auto_tracing(modules=["app"], min_duration=0)


if __name__ == "__main__":
    uvicorn.run("app.main:app", port=1703, reload=True)
