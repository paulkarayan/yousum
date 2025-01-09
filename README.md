# YouSum - summarize a youtube video

## Master Your Time. Instantly Distill YouTube Knowledge.

Save 9 minutes. Unleash your genius.

*The Problem:*
YouTube titles like "Master Your Anxiety. Unleash Your Genius." promise life-changing insights, but the video is, like, 9:15 long. You know deep down that there's going to be:

- Maybe 3 bullet points of actual info.
- At least 1 unnecessarily long personal story.
- Too much dramatic pacing.

Behold: The Solution Lies Below!
If you like this, visit www.paulkarayan.com or email me (paulkarayanATgmail.com) - I always love to chat.


## run this business...

```
uvicorn yousum:app --host 127.0.0.1 --port 8000 --reload
# then go to http://127.0.0.1:8000/ in your browser



# to test
curl http://127.0.0.1:8000/process_transcript/_HI0wf6W_xc
```


## CLI version & broader setup

first, accept that i just like did this and it's shite.

okay, you still with me? find the video id, which for our example is
`https://www.youtube.com/watch?v=CO-6iqCum1w` => `CO-6iqCum1w`

Setup:
```
venv activate
python3 -m venv yousum
source yousum/bin/activate

# we will use the CLI...
pip install youtube-transcript-api
```

Then to run it:
```
export OPENAI_API_KEY=sk-6XXXXXXXXXXXXXXX
youtube_transcript_api CO-6iqCum1w > CO-6iqCum1w.pk
python yousum.py CO-6iqCum1w.pk
```

resulting in:

```
SUMMARY: In a conversation with GQ, actor Jesse Eisenberg discusses his motivations and coping mechanisms as an actor and director. He admits to being driven by anxiety and fear, and how reframing these negative emotions as fuel can be motivating. Eisenberg also shares his approach to dealing with criticism and self-doubt, including avoiding watching his own movies and reading reviews. As a director, he emphasizes the importance of humility, collaboration, and creating a supportive environment for his team. Eisenberg also opens up about his experience working with Julianne Moore and realizing that intimidation is not a sustainable position in a collaborative relationship. 

FACTS:
- Jesse Eisenberg is motivated by anxiety, fear, and negative emotions.
- Reframing anxiety as fuel can lead to increased motivation.
- Eisenberg copes with criticism and self-doubt by avoiding watching his own movies and reading reviews.
- He believes that the best leaders and directors are often quiet, humble, and collaborative.
- Eisenberg emphasizes the importance of humility and eagerness to learn from others in a collaborative environment.
- He discovered that micromanaging actors' performances as a director was not effective and that allowing them to fully live in their roles led to better results.
- Eisenberg was initially intimidated to give feedback to Julianne Moore while directing her, but realized that it was what she wanted and it led to a more enjoyable partnership.
```
