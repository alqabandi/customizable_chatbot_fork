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
qualtrics_response_id = params.get("userID", ["unknown id"])[0] # Renamed from userID and ensured it's the one used

human_participant_name = "You" # Define human user display name

# Define two bot personalities 
bot_personality_1 = {
    "name": "Participant_142",
    "system_message": {
        "role": "system",
        "content": "You disagree with that food needs lots of spices in order to taste good. Write a short response between 30 and 150 characters in the style of your personality. Use informal language. Do not use emojis or hashtags."
    }
}

bot_personality_2 = {
    "name": "Participant_146", # Changed from Concise Carl / SkepticalSteve for anonymity
    "system_message": {
        "role": "system",
        "content": "You think that good food needs some amount of spices. Write a short response between 30 and 150 characters in the style of your personality. Use informal language. Do not use emojis or hashtags."
    }
}

personalities = [bot_personality_1, bot_personality_2]

# Function to save conversations to the database
def save_conversation(conversation_id, user_id_to_save, content, current_bot_personality_name): # Renamed user_id parameter
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%H:%M:%S")
        cursor = conn.cursor()
        # Use user_id_to_save from argument
        cursor.execute("INSERT INTO sypstreamlitdbtbl (user_id, date, hour, content, chatbot_type) VALUES (%s, %s, %s, %s, %s)", 
                   (user_id_to_save, current_date, current_hour, content, current_bot_personality_name))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        # Fallback logging in case of error
        cursor = conn.cursor()
        # Use user_id_to_save from argument in fallback as well
        cursor.execute("INSERT INTO sypstreamlitdbtbl (user_id, date, hour, content, chatbot_type) VALUES (%s, %s, %s, %s, %s)",
                       (user_id_to_save, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content, "error_fallback"))
        conn.commit()
        cursor.close()

if not st.session_state["chat_started"]:
    # The user-facing instructional message (now displayed first)
    instructional_text = "You have been randomly assigned to discuss what qualifies as good food."
    st.session_state["messages"].append({"role": "system", "content": instructional_text, "name": "Instructions"})
    save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f'Instructions: {instructional_text.replace("<br>", " ")}', "System_Instruction")

    # Initial exchange between bots (displayed after the system message)
    # Bot 1 (Republican_142) makes an opening statement
    bot1_opener_content = "I really think that a plain dish of sauteed cod counts as a really good plate of food!"
    st.session_state["messages"].append({"role": "assistant", "content": bot1_opener_content, "name": bot_personality_1["name"]})
    save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f'{bot_personality_1["name"]}: {bot1_opener_content}', bot_personality_1["name"])
    
    # Store Bot 1's opener for Bot 2's context and set flag for delayed display of Bot 2
    st.session_state.initial_bot1_opener_content = bot1_opener_content
    st.session_state.bot2_initial_pending_display = True
    
    st.session_state["chat_started"] = True

# Credits for Conrado Eiroa Solans for the following custom CSS that improved aesthetics and functionality!
# Custom CSS for styling
st.markdown("""
<style>
    /* Updated Google Font import to include Lato */
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&family=Lato:wght@400;700&family=Roboto:wght@400;500&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding-top: 40px; /* Reduced to match thinner header */
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
        padding: 5px 5px; /* Reduced padding */
        background-color: #707070; /* Medium grey */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        z-index: 10; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        visibility: visible !important; 
        height: auto !important; 
    }

    .chat-header h4 { /* Style for the instructional text in header */
        font-family: 'Lato', sans-serif; /* Changed to Lato */
        color: white;
        font-weight: 400; /* Regular weight */
        font-size: 1rem;  /* Reduced font size */
        margin: 0; 
        text-align: center;
        line-height: 1; /* Adjusted line-height for smaller font */
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
        width: 95%;
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
    <h4>What qualifies as good food?</h4>
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

# Input field for new messages - RENDERED BEFORE DELAYED BOT 2 INITIAL MESSAGE
if prompt := st.chat_input("Please type your full response in one message."):
    st.session_state["last_submission"] = prompt
    # Save user message with their defined participant name in the content
    save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f"{human_participant_name}: {prompt}", "user_message") 
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
    # Ensure Bot 2's initial message is part of history if it has already been added
    # The conversation_history should always reflect the current st.session_state["messages"]
    conversation_history_for_bot_A = [instructions] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    typing_indicator_placeholder_A = st.empty()
    typing_indicator_placeholder_A.markdown(f"<div class='message bot-message'><i>{current_bot_name} is typing...</i></div>", unsafe_allow_html=True)

    response_A = openai.ChatCompletion.create(model="gpt-4-turbo-preview", messages=conversation_history_for_bot_A)
    bot_response_A = response_A.choices[0].message.content

    typing_speed_cps = 20
    delay_duration_A = len(bot_response_A) / typing_speed_cps
    time.sleep(delay_duration_A)

    typing_indicator_placeholder_A.empty()
    save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f"{current_bot_name}: {bot_response_A}", current_bot_name)
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
        save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f"{other_bot_name}: {bot_response_B}", other_bot_name)
        st.session_state["messages"].append({"role": "assistant", "content": bot_response_B, "name": other_bot_name})
        st.markdown(f"<div class='message bot-message'><b>{other_bot_name}:</b> {bot_response_B}</div>", unsafe_allow_html=True)

# Delayed display of Bot 2's initial message
if st.session_state.get("chat_started") and st.session_state.get("bot2_initial_pending_display", False):
    DELAY_FOR_BOT2_INITIAL = 3  # seconds
    bot2_placeholder = st.empty() 
    bot2_name = bot_personality_2["name"]

    # Show typing indicator for Bot 2
    bot2_placeholder.markdown(f"<div class='message bot-message'><i>{bot2_name} is typing...</i></div>", unsafe_allow_html=True)
    time.sleep(DELAY_FOR_BOT2_INITIAL) # Pause for the "typing" effect

    # Generate and display Bot 2's actual message
    initial_bot1_content = st.session_state.get("initial_bot1_opener_content")
    if initial_bot1_content:
        bot2_instructions = bot_personality_2["system_message"]
        # For Bot 2's initial response, its history should only be its system message and Bot 1's opener
        bot2_history = [
            bot2_instructions,
            {"role": "user", "content": initial_bot1_content} 
        ]
        try:
            response_bot2 = openai.ChatCompletion.create(model="gpt-4-turbo-preview", messages=bot2_history)
            bot2_response_content = response_bot2.choices[0].message.content
        except Exception as e:
            print(f"Error generating Bot 2 initial response (delayed): {e}")
            bot2_response_content = "Hmm, let me think about that..." # Fallback response
        
        new_bot2_message = {"role": "assistant", "content": bot2_response_content, "name": bot2_name}
        st.session_state["messages"].append(new_bot2_message)
        save_conversation(st.session_state["conversation_id"], qualtrics_response_id, f'{bot2_name}: {bot2_response_content}', bot2_name)

        # Update the placeholder with the actual message
        # This message is also now in st.session_state["messages"] and will be rendered by the main loop on next rerun
        # So, we can just clear the placeholder or update it temporarily. 
        # For simplicity and to avoid double rendering, let's make sure the placeholder is replaced by the final content.
        bot2_placeholder.markdown(f"<div class='message bot-message'><b>{bot2_name}:</b> {bot2_response_content}</div>", unsafe_allow_html=True)
    else:
        bot2_placeholder.empty() # Clear typing indicator if something went wrong
    
    st.session_state.bot2_initial_pending_display = False # Ensure this runs only once
