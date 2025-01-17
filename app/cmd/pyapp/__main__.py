import os

from dotenv import load_dotenv

if __name__ == "__main__":
    env_path = os.environ.get("MYAPP_ENV_PATH", "../local.env")
    load_dotenv(dotenv_path=env_path)

    from .main import main

    try:
        main()
    except KeyboardInterrupt:
        print("Bye!")
