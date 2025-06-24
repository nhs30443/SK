import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Config:
    """アプリケーション設定クラス"""

    # 基本設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Gemini API設定
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get('GEMINI_MAX_OUTPUT_TOKENS', 1024))
    GEMINI_TEMPERATURE = float(os.environ.get('GEMINI_TEMPERATURE', 0.7))

    # 問題生成設定
    MAX_GENERATION_TIME = int(os.environ.get('MAX_GENERATION_TIME', 10))
    USE_FALLBACK_ON_ERROR = os.environ.get('USE_FALLBACK_ON_ERROR', 'True').lower() == 'true'
    BATCH_GENERATION_SIZE = int(os.environ.get('BATCH_GENERATION_SIZE', 5))

    # レート制限設定（Geminiは制限が緩い）
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 1000))
    RATE_LIMIT_PER_DAY = int(os.environ.get('RATE_LIMIT_PER_DAY', 50000))

    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @staticmethod
    def validate_config():
        """設定の妥当性をチェック"""
        issues = []

        if not Config.GEMINI_API_KEY:
            issues.append("Gemini APIキーが設定されていません")

        if Config.MAX_GENERATION_TIME < 1:
            issues.append("MAX_GENERATION_TIMEは1以上である必要があります")

        if Config.GEMINI_TEMPERATURE < 0 or Config.GEMINI_TEMPERATURE > 2:
            issues.append("GEMINI_TEMPERATUREは0-2の範囲である必要があります")

        if Config.BATCH_GENERATION_SIZE < 1 or Config.BATCH_GENERATION_SIZE > 20:
            issues.append("BATCH_GENERATION_SIZEは1-20の範囲である必要があります")

        return issues


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    TESTING = False

    @staticmethod
    def validate_production():
        issues = Config.validate_config()

        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            issues.append("本番環境では安全なSECRET_KEYを設定してください")

        return issues


class TestingConfig(Config):
    """テスト環境設定"""
    DEBUG = True
    TESTING = True
    GEMINI_API_KEY = 'test-key'


# Gemini API制限情報
GEMINI_LIMITS = {
    'free_tier': {
        'requests_per_minute': 15,
        'requests_per_day': 1500,
        'tokens_per_minute': 32000,
        'tokens_per_day': 50000,
        'models_available': ['gemini-1.5-flash', 'gemini-1.5-pro']
    },
    'paid_tier': {
        'requests_per_minute': 1000,
        'requests_per_day': 50000,
        'tokens_per_minute': 4000000,
        'tokens_per_day': 4000000,
        'models_available': ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    }
}

# 環境に応じた設定を選択
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}