from hero.config import Settings


def main() -> None:
    settings = Settings()
    print(f"Hero voice agent starting (model={settings.ollama_model})...")


if __name__ == "__main__":
    main()
