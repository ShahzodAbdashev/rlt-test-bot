from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings  


class Settings(BaseSettings):
	bot_token: str = Field(..., alias="BOT_TOKEN")
	openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
	# PostgreSQL settings
	db_host: str = Field("localhost", alias="DB_HOST")
	db_port: int = Field(5432, alias="DB_PORT")
	db_name: str = Field("rlt_test_bot", alias="DB_NAME")
	db_user: str = Field("postgres", alias="DB_USER")
	db_password: str = Field("", alias="DB_PASSWORD")
	

	@property
	def db_url(self) -> str:
		return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

	model_config = SettingsConfigDict(
		case_sensitive = False,
		env_file = ".env",
		env_file_encoding = "utf-8",
	)


settings = Settings()