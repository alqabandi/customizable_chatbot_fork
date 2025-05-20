import openai
import streamlit as st
from datetime import datetime
import mysql.connector
import uuid
import random
import time

# Initialize session state for message tracking and other variables
if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Set up OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# If the user_id hasn't been set in session_state yet, try to retrieve it 
js_code = """
<div style="color: black;">
    <script>
        setTimeout(function() {
            const userID = document.getElementById("userID").value;
            if (userID) {
                window.Streamlit.setSessionState({"user_id": userID});
            }
        }, 1000);  // Delaying the execution by 1 second to ensure DOM is ready
    </script>
</div>
"""
st.markdown(js_code, unsafe_allow_html=True)
user_id = st.session_state.get('user_id', 'unknown_user_id')  # Replace with your actual user identification method

# Database connection
conn = mysql.connector.connect(
    user=st.secrets['sql_user'],
    password=st.secrets['sql_password'],
    database=st.secrets['sql_database'],
    host=st.secrets['sql_host'],
    port=st.secrets['sql_port'],
    charset='utf8mb4'
)

# Create output table
def create_conversations_table():
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sypstreamlitdbtbl (
        user_id VARCHAR(255),
        date VARCHAR(255),
        hour VARCHAR(255),
        content MEDIUMTEXT,
        chatbot_type VARCHAR(255)
    )
    ''')
    conn.commit()
    cursor.close()

# Ensure the table is created before trying to save to it
create_conversations_table()

#Get userID for the table
params = st.experimental_get_query_params()
userID = params.get("userID", ["unknown id"])[0]

human_participant_name = "Participant_147" # Define human user display name

# Define two bot personalities for Republicans against Ukraine aid
bot_personality_1 = {
    "name": "Participant_142",
    "system_message": {
        "role": "system",
        "content": "You love to play DND and have an active imagination. Write a short response between 30 and 150 characters in the style of your personality. Use informal language. Do not use emojis or hashtags."
    }
}

bot_personality_2 = {
    "name": "Participant_146", # Changed from Concise Carl / SkepticalSteve for anonymity
    "system_message": {
        "role": "system",
        "content": "You just found out you have aphantasia, a condition where you cannot imagine visual scenes in your mind, and that's given you an existential crisis. Write a short response between 30 and 150 characters in the style of your personality. Use informal language. Do not use emojis or hashtags."
    }
}

personalities = [bot_personality_1, bot_personality_2]

# Function to save conversations to the database
def save_conversation(conversation_id, user_id, content, current_bot_personality_name):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%H:%M:%S")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sypstreamlitdbtbl (user_id, date, hour, content, chatbot_type) VALUES (%s, %s, %s, %s, %s)", 
                   (userID, current_date, current_hour, content, current_bot_personality_name)) # Use current_bot_personality_name
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        # Fallback logging in case of error - consider if current_bot_personality_name should be included here too
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sypstreamlitdbtbl (user_id, date, hour, content, chatbot_type) VALUES (%s, %s, %s, %s, %s)",
                       (userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content, "error_fallback"))
        conn.commit()
        cursor.close()

if not st.session_state["chat_started"]:
    # The user-facing instructional message (now displayed first)
    instructional_text = "You have been randomly assigned to discuss the topic of imagination and creativity."
    st.session_state["messages"].append({"role": "system", "content": instructional_text, "name": "Instructions"})
    save_conversation(st.session_state["conversation_id"], user_id, f'Instructions: {instructional_text.replace("<br>", " ")}', "System_Instruction")

    # Initial exchange between bots (displayed after the system message)
    # Bot 1 (Participant_142) makes an opening statement
    bot1_opener_content = "I have a really active imagination!! It's why i love to play DND with friends"
    st.session_state["messages"].append({"role": "assistant", "content": bot1_opener_content, "name": bot_personality_1["name"]})
    save_conversation(st.session_state["conversation_id"], user_id, f'{bot_personality_1["name"]}: {bot1_opener_content}', bot_personality_1["name"])

    # Bot 2 (Participant_146) responds to Bot 1
    bot2_instructions = bot_personality_2["system_message"]
    bot2_history = [
        bot2_instructions,
        # IMPORTANT: For Bot 2 to respond to Bot 1, Bot 1's message must be in the history passed to the API.
        # However, since we are just setting up the initial display, Bot 1's message is already added above.
        # For the API call for Bot 2, we use Bot 1's opener as if it were a user prompt to Bot 2.
        {"role": "user", "content": bot1_opener_content} 
    ]
    
    try:
        response_bot2 = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=bot2_history
        )
        bot2_response_content = response_bot2.choices[0].message.content
    except Exception as e:
        print(f"Error generating Bot 2 initial response: {e}")
        bot2_response_content = "Hmmmm, yeah i guess.." # Fallback response

    st.session_state["messages"].append({"role": "assistant", "content": bot2_response_content, "name": bot_personality_2["name"]})
    save_conversation(st.session_state["conversation_id"], user_id, f'{bot_personality_2["name"]}: {bot2_response_content}', bot_personality_2["name"])
    
    st.session_state["chat_started"] = True

# Credits for Conrado Eiroa Solans for the following custom CSS that improved aesthetics and functionality!
# Custom CSS for styling
st.markdown("""
<style>
    /* Updated Google Font import to include Comfortaa */
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&family=Roboto:wght@400;500&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding-top: 60px; /* Ensure space for the fixed custom header */
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: #EEE;
    }
            
    .chat-header {
        position: fixed; /* make "width: 44rem" if want to use full screen (but creates little visual bug in qualtrics) */
        top: 0px; /* Increased to move the header lower */
        left: 0;
        right: 0;
        display: flex;
        align-items: center;
        justify-content: center; /* Center the text in the header */
        padding: 10px;
        background-color: #707070; /* Medium grey */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        z-index: 10; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        visibility: visible !important; 
        height: auto !important; 
    }

    .chat-header h4 { /* Style for the instructional text in header */
        font-family: 'Roboto', sans-serif; /* Changed from Comfortaa for better readability of longer text */
        color: white;
        font-weight: 500; /* Medium weight */
        font-size: 0.9rem; /* Adjust size to fit text */
        margin: 0; 
        text-align: center;
    }
        
    /* .circle-logo rule removed */
            
    .chat-container {
        flex-grow: 1;
        margin: 2rem auto 0 auto;
        overflow-y: auto;
        position: relative;
        box-sizing: border-box;
    }
    .message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 70%;
        position: relative;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        border-top-right-radius: 0;
        text-align: left;
    }
    .bot-message {
        background-color: #f1f1f1;
        color: #333;
        margin-right: auto;
        border-top-left-radius: 0;
        text-align: left;
    }
    .system-prompt { /* New style for the system instructional message */
        margin: 15px 0;
        padding: 10px;
        border-radius: 10px;
        background-color: #e0e0e0; /* Light grey background */
        color: #111; /* Darker text */
        font-family: 'Georgia', serif; /* Different font */
        text-align: center;
        border: 1px dashed #aaa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* CSS to hide the default Streamlit header */
    [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Fallback for other potential header elements if the above is not enough */
    /* You might need to inspect the Streamlit app in your browser's developer tools */
    /* to find the exact selectors if the header persists. */
    /* For example, the main app container's direct header child: */
    div[data-testid="stApp"] > header {
        display: none !important;
        visibility: hidden !important;
    }
    /* Ensure body has no top padding if Streamlit header is gone */
    /* and you are not using your own fixed custom header */
    body > #root > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) {
        padding-top: 0 !important;
    }

    /* CSS to hide the "Running..." status indicator */
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Comprehensive Streamlit UI hiding rules from forum post */
    div[data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    div[data-testid="stDecoration"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    div[data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    #MainMenu {
        visibility: hidden;
        height: 0%;
    }
    header { /* This is a general HTML element selector, could affect your custom .chat-header */
        visibility: hidden;
        height: 0%;
    }
    footer {
        visibility: hidden;
        height: 0%;
    }

    /* CSS to hide anchor links from headers (h1-h6) */
    h1 > div > a, 
    h2 > div > a, 
    h3 > div > a, 
    h4 > div > a, 
    h5 > div > a, 
    h6 > div > a {
        display: none !important; /* Ensure it overrides Streamlit's default */
    }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <h4>You have been randomly assigned to discuss the topic of imagination and creativity.</h4>
</div>
<div class="chat-container">
    <!-- Your messages will be inserted here by Streamlit -->
</div>
""", unsafe_allow_html=True)

# Display messages using markdown to apply custom styles
for message in st.session_state["messages"]:
    message_class = "user-message" if message["role"] == "user" else ("bot-message" if message["role"] == "assistant" else "system-prompt")
    
    if message["role"] == "system": # Handle system/instructional messages
        st.markdown(f"<div class='{message_class}'>{message['content']}</div>", unsafe_allow_html=True)
    elif (message["role"] == "assistant" or message["role"] == "user") and "name" in message:
        st.markdown(f"<div class='message {message_class}'><b>{message['name']}:</b> {message['content']}</div>", unsafe_allow_html=True)
    elif message["role"] == "assistant": # Fallback for assistant messages without name (e.g. very old initial)
        st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)
    else: # Fallback for user messages if name somehow not set (should not happen with new logic)
        st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Input field for new messages
if prompt := st.chat_input("Please type your full response in one message."):
    st.session_state["last_submission"] = prompt
    # Save user message with their defined participant name in the content
    save_conversation(st.session_state["conversation_id"], user_id, f"{human_participant_name}: {prompt}", "user_message") 
    # Add user message to session state with name attribute
    st.session_state["messages"].append({"role": "user", "content": prompt, "name": human_participant_name})
    message_class = "user-message"
    # Immediately display the participant's message with their name
    st.markdown(f"<div class='message {message_class}'><b>{human_participant_name}:</b> {prompt}</div>", unsafe_allow_html=True)

    # Bot A (chosen_personality) responds to the user
    chosen_personality = random.choice(personalities)
    current_bot_name = chosen_personality["name"]
    start_message = chosen_personality["system_message"]
    instructions = start_message
    conversation_history_for_bot_A = [instructions] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    typing_indicator_placeholder_A = st.empty()
    typing_indicator_placeholder_A.markdown(f"<div class='message bot-message'><i>{current_bot_name} is typing...</i></div>", unsafe_allow_html=True)

    response_A = openai.ChatCompletion.create(model="gpt-4-turbo-preview", messages=conversation_history_for_bot_A)
    bot_response_A = response_A.choices[0].message.content

    typing_speed_cps = 20
    delay_duration_A = len(bot_response_A) / typing_speed_cps
    time.sleep(delay_duration_A)

    typing_indicator_placeholder_A.empty()
    save_conversation(st.session_state["conversation_id"], user_id, f"{current_bot_name}: {bot_response_A}", current_bot_name)
    st.session_state["messages"].append({"role": "assistant", "content": bot_response_A, "name": current_bot_name})
    st.markdown(f"<div class='message bot-message'><b>{current_bot_name}:</b> {bot_response_A}</div>", unsafe_allow_html=True)

    # Probabilistic response from Bot B to Bot A
    probability_bot_to_bot_reply = 0.5 # 50% chance for Bot B to reply to Bot A
    if random.random() < probability_bot_to_bot_reply:
        # Determine Bot B (the other bot)
        if chosen_personality == personalities[0]:
            other_bot_personality = personalities[1]
        else:
            other_bot_personality = personalities[0]
        
        other_bot_name = other_bot_personality["name"]
        other_bot_start_message = other_bot_personality["system_message"]
        
        # Conversation history for Bot B includes Bot A's latest message
        conversation_history_for_bot_B = [other_bot_start_message] + \
                                         [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
        
        typing_indicator_placeholder_B = st.empty()
        typing_indicator_placeholder_B.markdown(f"<div class='message bot-message'><i>{other_bot_name} is typing...</i></div>", unsafe_allow_html=True)

        response_B = openai.ChatCompletion.create(model="gpt-4-turbo-preview", messages=conversation_history_for_bot_B)
        bot_response_B = response_B.choices[0].message.content

        delay_duration_B = len(bot_response_B) / typing_speed_cps
        time.sleep(delay_duration_B)

        typing_indicator_placeholder_B.empty()
        save_conversation(st.session_state["conversation_id"], user_id, f"{other_bot_name}: {bot_response_B}", other_bot_name)
        st.session_state["messages"].append({"role": "assistant", "content": bot_response_B, "name": other_bot_name})
        st.markdown(f"<div class='message bot-message'><b>{other_bot_name}:</b> {bot_response_B}</div>", unsafe_allow_html=True)
