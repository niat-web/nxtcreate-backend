import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Setup Environment
load_dotenv()

# Initialize the Vertex AI Client
client = genai.Client(
    vertexai=True, 
    project=os.getenv("GOOGLE_CLOUD_PROJECT"), 
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def generate_video_from_local_assets(local_image_path, output_filename):
    """
    Reads a local image, sends it as a reference for video generation,
    and downloads the resulting video locally.
    """
    
    # Verify the local file exists before starting
    if not os.path.exists(local_image_path):
        print(f"❌ Error: Local file '{local_image_path}' not found.")
        return

    print(f"🚀 Reading local image: {local_image_path}")
    
    try:
        # 2. Read the local image file as bytes
        with open(local_image_path, "rb") as f:
            image_bytes = f.read()

        # Determine mime type based on extension
        mime_type = "image/png" if local_image_path.lower().endswith(".png") else "image/jpeg"

        print("🎬 Sending request to Veo (this may take a few minutes)...")
        
        # 3. Start the generation operation
        # Note: output_gcs_uri is OMITTED so we get bytes back directly
        operation = client.models.generate_videos(
            model="veo-3.1-generate-001",
            prompt="Create a 3D video nameing the product as 'spraymint' this text will display in here in a very lucarative manner",
            config=types.GenerateVideosConfig(
                reference_images=[
                    types.VideoGenerationReferenceImage(
                        image=types.Image(
                            image_bytes=image_bytes,
                            mime_type=mime_type,
                        ),
                        reference_type="asset",
                    ),
                ],
                aspect_ratio="9:16",
            ),
        )

        # 4. Polling loop
        while not operation.done:
            print("⏳ Video is being generated... checking again in 15s")
            time.sleep(15)
            operation = client.operations.get(operation)

        # 5. Handle the result
        if operation.result and operation.result.generated_videos:
            output_dir = "output_folder"
            os.makedirs(output_dir, exist_ok=True)
            save_path = os.path.join(output_dir, output_filename)
            
            video_obj = operation.result.generated_videos[0].video
            
            # 6. Download the bytes to a local file
            if video_obj.video_bytes:
                print(f"📥 Generation complete! Saving to {save_path}...")
                with open(save_path, "wb") as f:
                    f.write(video_obj.video_bytes)
                print(f"✅ Success! File saved at: {os.path.abspath(save_path)}")
            else:
                print(f"⚠️ Video was generated but bytes weren't returned. URI: {video_obj.uri}")
        else:
            print("❌ Operation finished, but no video was found in the response.")

    except Exception as e:
        print(f"⚠️ An error occurred: {e}")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Replace 'my_mango_bottle.png' with your actual filename
    INPUT_IMAGE = "spraymintt_premium_photoshoot.png" 
    OUTPUT_NAME = "spraymintt_premium_photoshoot.mp4"
    
    generate_video_from_local_assets(INPUT_IMAGE, OUTPUT_NAME)