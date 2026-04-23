# Installation 

1. Clone the repo:

        git clone https://github.com/enfyna/fchat --depth=1
        cd fchat

2. Install requirements:

        uv venv --python 3.11
        uv pip install -r requirements.txt

> [!NOTE]
> If you have missing dependencies check 'shell.nix' for used packages.

3. Create .env file:
        
        mv .env.example .env

4. Set the variables. (Set the PREFIX variable to a folder where you want to generate your shorts into):

        # .env
        OPENROUTER_API_KEY=... 
        PREFIX=/home/enfyna/Documents/generate_fchat/

5. Create 'prompt.txt' file inside your PREFIX folder:

        cd /home/enfyna/Documents/generate_fchat/
        touch prompt.txt

> [!TIP]
> You can use this as the prompt:

        Generate exactly two output files and nothing else. Do not include explanations, commentary, or extra text.

        1. script.txt
           - Content: Write a 30-second YouTube Shorts script that clearly and engagingly explains what the event, person, or trend is
           - Maintain a conversational, fast-paced, and easy-to-follow tone suited for short-form video
           - Use short sentences, natural transitions, and active voice.
           - The script will be read by the Chatterbox TTS model, so write it in a way that prevents stuttering.
           - The first sentence must be a strong hook that grabs attention within the first 3 seconds.
           - Make sure given information is accurate and up-to-date.
           - Style: clear, structured, and conversational.
           - When writing hours, do not include minutes or time-zone information. Use only this format: 10 PM, 6 AM.
           - Never use abbreviations like OMG, LOL, or SMH. You may use only technical abbreviations such as DNS, HTTPS, or PC.

        2. youtube.txt
           - Content: A valid JSON object with YouTube metadata.
           - Must include:
             "snippet" with:
                - "title": a catchy title with strong SEO keywords, add relevant hashtags
                - "description": a clear summary of the video content with relevant keywords, add relevant hashtag
                - "tags": a list of highly relevant keywords for discoverability
                - "categoryId": the most appropriate YouTube category (pick correctly, do not default to 22 unless it fits) 
             "status" with: 
                - "privacyStatus": "private"
                - "publishAt": the scheduled date and time in ISO 8601 format, exactly as given below
                - "selfDeclaredMadeForKids": false

        ⚠️ Rules:
        - Output must strictly be inside one single block with no extra characters.
        - Inside that block, include exactly two sections:
          First `script.txt` followed by the script text.
          Then `youtube.txt` followed by the JSON object.
        - Do NOT output anything else.
        - Never reuse example content, only follow the structure.
        - Ensure the script and metadata are aligned with the topic.

# Usage

1. This will generate a folder in the PREFIX folder. 

        ./fauto.py

2. This will search for the folders and generate the videos.

        ./generate.py

3. If you created a google console project you can use this to upload the video to youtube:

        ./upload_yt.py

