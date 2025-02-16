# Customizable chatbot

This repository provides the instructions and code needed to create a customized chatbot that can be embedded into a Qualtrics survey. You can define various model parameters to achieve the desired chatbot behavior. Additionally, the code includes an option for randomization, allowing you to use different model specifications to compare behaviors. This enables easy customization of LLMs to suit your requirements and facilitates their integration into Qualtrics for conducting experiments.

## FIRST, you'll need:
- An account with the OpenAI API.
You'll need to set up a payment method and get an API key (https://platform.openai.com/docs/api-reference/authentication).

- A mySQL database hosted online.
In this tutorial, I'll be using google cloud for hosting. It's one of the easiest ways to do it. If you want to do it the same way, you'll have to create an account and set up payment method.(https://console.cloud.google.com).

- A Streamlit account.
A free account works.

- A Github account.
You need it to host your repository from which streamlit will pull the code.

- A code editor installed on your computer. I recommend VSCode. 

### Step 1: Fork it
Fork this repository in your own github. This will create a copy of all these files in your own github account. 

### Step 2: OpenAI API key
Figure out your OpenAI API key and the credentials for the google cloud SQL databsabe.

### Step 3: Set up MySQL database on Google Cloud
Create an account on console.cloud.google.com.
On the search bar, look for SQL. Create a Cloud SQL instance. It will take a few minutes for this operation to finish.
In the "overview" page of your instance, open the "databases" tab and create a new database. Give the database a name related to your project.
When you're creating the database, you will some passowords and keys to access your database. Make sure to save all those fields, especially the instance password. Save it somewhere.
Once your instance and database are created, you will have to create a table inside the database.
To create a table, the first thing you should do is to activate the cloud shell. 
Make sure that you're in the correct project. Once in the right project, run the following command (make sure to change INSTANCE_NAME. if you set up a different user, you might have to update it as well)
```
gcloud sql connect INSTANCE_NAME --user=root
```
After successfully connecting to your instance, you'll be prompted to input the instance password. Paste it in there and press enter.
If your password is correct, you should be on a SQL environment.

Create a new table with the fields that you'll need. By deafault, the chatbot fields are user_id (matched with response id from qualtrics), date, hour, content (the actual messages sent), and chatbot type (if you have multiple chatbot types, this will be the type of chatbot that the participant was talking to). To create a table like that, you should run the following command (make sure to change table_name to a name that makes sense for your project):
```
CREATE TABLE table_name (
        user_id VARCHAR(255),
        date VARCHAR(255),
        hour VARCHAR(255),
        content MEDIUMTEXT,
        chatbot_type VARCHAR(255)
    );
```

To make sure it works properly, you can run the following command and check if your new table is listed:
```
SHOW TABLES;
```

### Step 4: Streamlit
Create a new app on streamlit. When prompted to select the source, select the forked github repo as the source.
After your app is created, go to app settings and set up all the secrets in there (API_KEY, sql_user, sql_password, sql_host, sql_port, sql_database).

### Step 5: Qualtrics
Create a new qualtrics survey and create a Text/Graphic question.
Under "Question Behavior" select "javascript".
Paste the following code (make sure to substitute the values in [YOUR-DOMAIN] by the name of your streamlit app and PLACEHOLDER by chatbot type).

```
Qualtrics.SurveyEngine.addOnload(function() {
    // Create the iframe element
    var iframe = document.createElement('iframe');
    var userID = "${e://Field/ResponseID}";  // Fetch the ResponseID from Qualtrics

    // Set the source of the iframe to your chatbot's URL
    iframe.src = "https://[YOUR-DOMAIN].streamlit.app/?type=PLACEHOLDER&embedded=true&userID=${e://Field/ResponseID}";

    // Increase the height of the iframe
    iframe.style.width = '100%';  // Take the full width of the parent container
    iframe.style.height = '550px'; // Adjust the height to show more content
    iframe.style.border = 'none';  // Remove any default borders
    iframe.style.overflow = 'hidden';  // Hide overflow content

    // Find a placeholder in your Qualtrics question
    var placeholder = document.getElementById('chatbotPlaceholder');
    placeholder.style.position = 'relative';
    placeholder.style.overflow = 'hidden'; // Ensure container overflow is hidden

    // Append the iframe to the placeholder
    placeholder.appendChild(iframe);

    // Create a mask to hide the bottom 50px that contains the streamlit logo
    var maskDiv = document.createElement('div');
    maskDiv.style.position = 'absolute';
    maskDiv.style.bottom = '0';
    maskDiv.style.left = '0';
    maskDiv.style.width = '100%';
    maskDiv.style.height = '60px';  // Adjust height as needed to cover the icons
    maskDiv.style.backgroundColor = 'white';  // Match background color of your app
    maskDiv.style.zIndex = '9999';  // Ensure it sits on top of the iframe

    // Append the mask div on top of the iframe
    placeholder.appendChild(maskDiv);
});
```

In addition to the javascript, you need to add the chatbot element to html.

Go to the question where you want to display the chatbot. Click on the question to edit it and select "HTML View". Paste the following following element by the end of the text:

```
<div id="chatbotPlaceholder">&nbsp;</div>
```

If you want to have multiple chatbots with different behaviors (and participants to be randomly assigned to one of them), you'll have to do the randomization through qualtrics.
You will create several questions, each question containing a different chatbot (bot type can be defined by changing 'type=PLACEHOLDER' in the bot url). Then, under 'Survey flow', you can use a randomizer with an embedded data field to select the bot type. It should look something like this:
<img width="1161" alt="image" src="https://github.com/user-attachments/assets/1ea9d803-eac6-4c95-8480-c561de868364" />

Once that's done, you will use the branch function to allocate each person to their respective bots. If they were randomly assigned to bot type 1, then make sure to display bot type 1. Here's an example of what it should look like:

<img width="1109" alt="image" src="https://github.com/user-attachments/assets/26cab8f9-1bfa-41e5-a474-25ac4e95867f" />


### Step 6: Publish the survey and test it.
For testing, you'll chat with the chatbot. I recommend it chatting several times and having other people talk to it in order to test it. To make sure it's working:
- ensure there are no error messages;
- ensure that your data is recorded properly on your database by downloading it from google cloud and checking if all fields are filled correctly (user id, date, time, content);
- ensure that the bot is giving you the desired responses given the user message.


#### Important note on tokens and participants limits
The amount of participants that can simultaneously talk to the chatbot depend on the number of tokens you can send per minute. That limit is defined by your OpenAI account Tier. In tier 1 (as of 2024), there is a limit of 10,000 tokens per minute with GPT4. 10,000 tokens is about 75 messages per minute (assuming an average of 100 words per message and 1 token per 3/4 word). Assuming a high ceiling of 5 messages per minute, you should allow only 15 participants talking to the bot at a time. This estimation matches my personal experience collecting data with participants, where the chatbot starts to crash if more then 15 people are concurrently chatting with it.

If your OpenAI account has a higher tier, your limit my be a lot higher. As my account became Tier 3, the API allowed for 600,000 tokens per minute (GPT4), which translated to 900 people talking to chatbot concurrently (considering the same assumptions of messages per minute, words per message, and tokens per word as above.) 

### Step 7: Customize it!
Now that the app is working, customize the app. To change the chatbot behavior, there are two main things you can do:
1) change the message on "start_message", where we tell the system how to behave. In the world of LLMs, this is known as the system prompt. If you want to know the best strategies for creating good prompts, OpenAI has a guide: https://platform.openai.com/docs/guides/prompt-engineering
2) Changing and adding arguments to the "openai.ChatCompletion.create". There are many thing you can change (max number of tokens used, you can penalize certain words to decrease their frequency, change system temperature, etc.). You can check how to do it in https://platform.openai.com/docs/guides/gpt

#### Update 06/03/24
Thanks to Conrado Eiroa Solans, this web app now works better.
Issues fixed: 
- participants can now send the message by just pressing enter
- conversation is scrolled down automatically
- appearance is better

# How to cite this
Oldemburgo de Mello, Victoria. 2024. Customizable chatbot. GitHub. github.com/vicomello/customizable_chatbot


