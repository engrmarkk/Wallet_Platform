import cloudinary
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),  # duwyopabr
    api_key=os.getenv("API_KEY"),  # 827963865175173
    api_secret=os.getenv("API_SECRET")  # qBPWszxprbof_v9mVuhknZznk90
)
