import openai
import streamlit as st
from datetime import datetime
import mysql.connector
import uuid

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
    CREATE TABLE IF NOT EXISTS conversations (
        user_id VARCHAR(255),
        date VARCHAR(255),
        hour VARCHAR(255),
        content MEDIUMTEXT,
        chatbot_type VARCHAR(255)
    )
    ''')
    conn.commit()
    cursor.close()


#Get userID for the table
params = st.experimental_get_query_params()
userID = params.get("userID", ["unknown id"])[0]
# Get the query parameters
params = st.experimental_get_query_params()
userID = params.get("userID", ["unknown id"])[0]
# getting type of bot from url params
bot_type = params.get("HighPsych", ["unknown bot type"])[0]


# Function to save conversations to the database
def save_conversation(conversation_id, user_id, content):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%H:%M:%S")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, date, hour, content, chatbot_type) VALUES (%s, %s, %s, %s, %s)", 
                   (userID, current_date, current_hour, content, bot_type))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, date, hour, content) VALUES (%s, %s, %s, %s)",
                       (userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
        conn.commit()
        cursor.close()


if not st.session_state["chat_started"]:
    # Assuming this block is correctly executed when the app first loads
    initial_bot_message = "Hello SPRG!"
    st.session_state["messages"].append({"role": "assistant", "content": initial_bot_message})
    st.session_state["chat_started"] = True

# Credits for Conrado Eiroa Solans for the following custom CSS that improved aesthetics and functionality!
# Custom CSS for styling
st.markdown("""
<style>
    <div class="chat-header">
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding-top: 60px;
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
        padding: 10px;
        background-color: #333333; /* Darker background for the header */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        z-index: 1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
        
            
    .circle-logo {
        height: 40px;
        width: 40px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 10px;
    }
            
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

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <div class="circle-logo"></div> 
    <h4>Kit</h4>
</div>
<div class="chat-container">
    <!-- Your messages will be inserted here by Streamlit -->
</div>
""", unsafe_allow_html=True)

# Credits for Conrado Eiroa Solans for the following code that improved functionality!
# Display messages using markdown to apply custom styles
for message in st.session_state["messages"]:
    message_class = "user-message" if message["role"] == "user" else "bot-message"
    st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# If bot type =1, then bot is high in psychology. If bot type =0, then bot it is neutral
if bot_type == "1":
    start_message = {
        "role": "system", 
        "content": "You are a helpful and nice 50-year old human secretary who is passionate about your job. You answer things personally. You can answer all questions personally. During the conversations, Never mention: your age, name, that you're human, or that you're a secretary. You just behave naturally. You are now talking to a friend of yours, so act friendly and open."}
else:
    start_message = {
        "role": "system", 
        "content": "You are a conversational chatbot. Whenever someone asks you something, you try to answer the question to the best of your abilities. You do not deflect from questions. You should keep the conversation going."}


# Input field for new messages
if prompt := st.chat_input("Please type your full response in one message."):
    st.session_state["last_submission"] = prompt
    save_conversation(st.session_state["conversation_id"], "user_id", f"You: {prompt}")
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Immediately display the participant's message using the new style
    message_class = "user-message"
    st.markdown(f"<div class='message {message_class}'>{prompt}</div>", unsafe_allow_html=True)

    # Prepare the conversation history for OpenAI API
    instructions = start_message
    conversation_history = [instructions] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    # Call OpenAI API and display bot's response 
    response = openai.ChatCompletion.create(model="gpt-4-turbo-preview", 
                                            messages=conversation_history)

    bot_response = response.choices[0].message.content
    save_conversation(st.session_state["conversation_id"], "user_id", f"Alex: {bot_response}")
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    # Display the bot's response using the new style
    message_class = "bot-message"
    st.markdown(f"<div class='message {message_class}'>{bot_response}</div>", unsafe_allow_html=True)