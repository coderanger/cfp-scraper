# CFP-Scraper

This is web scraper that powers cfpcalendar.com.

Data is collected from various sources and written to Airtable. 

## Running it for yourself

Things you'll need: 

1. [Airtable](https://airtable.com/) account
2. Twitter account 
3. Python 3 + virtualenv

### Pre-reqs 

#### Airtable

1. Once you've created an Airtable account, use [this link](https://airtable.com/addBaseFromShare/shrYiAKkEEBMuVzcu?utm_source=airtable_shared_application) to copy the template Base to your own workspace. 

2. From https://airtable.com/account generate your API key and make a note of this. This will be your `AIRTABLE_API_KEY`. 

3. Go to https://airtable.com/api and select your base (the one to which you copied the source one in step 1 above). The URL you go to will look like `https://airtable.com/appXXXXXXYYYYY/api/docs` - make a note of the `appXXXXXXYYYYY`. This will be your `AIRTABLE_BASE_KEY`

#### Twitter

Create yourself API keys from https://developer.twitter.com/en/apps. 

#### Set up Python virtualenv

The easiest way to run this is in isolation, using virtualenv. 

1. Clone the git repo 

        git clone git@github.com:coderanger/cfp-scraper.git

2. Create virtualenv

        cd cfp-scraper
        virtualenv --python=python3 .
        source ./bin/activate.fish

    (Use the `activate` script appropriate for your shell)

3. Install required modules

        pip install -r requirements.txt

### Run cfp-scraper

* Activate the virtualenv

        source ./bin/activate.fish

    (Use the `activate` script appropriate for your shell)

* Based on the credentials obtained above, run: 

        ```
        export TWITTER_CONSUMER_KEY=xxxxxx
        export TWITTER_CONSUMER_SECRET=xxxxxx
        export TWITTER_ACCESS_KEY=xxxxxx
        export TWITTER_ACCESS_SECRET=xxxxxx

        export AIRTABLE_API_KEY=xxxxxx
        export AIRTABLE_BASE_KEY=xxxxxx
        ```

* Launch: 

        python main.py
