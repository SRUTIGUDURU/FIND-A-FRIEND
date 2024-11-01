from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from supabase import create_client, Client
import sqlite3

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Supabase connection
supabase_url = 'https://okmzzeoaqkllbzpyynnl.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDEzMTk3NCwiZXhwIjoyMDQ1NzA3OTc0fQ.cHSUjQBxC4ULt5bVEtyRb7AsUPPpxlB_jET2mJJEGiU'  
supabase: Client = create_client(supabase_url, supabase_key)

# SQLite connection for chat storage
conn = sqlite3.connect('db/chat_messages.db', check_same_thread=False)
c = conn.cursor()

# Ensure chat table exists
c.execute('''CREATE TABLE IF NOT EXISTS messages (
               group_name TEXT,
               email TEXT,
               message TEXT,
               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
           )''')
conn.commit()

# Fetch groups for user from Supabase
def get_user_groups(email):
    response = supabase.from_("groups").select("*").like("email", f"%{email}%").execute()
    if response.error:
        print("Error fetching groups:", response.error)
        return []
    return response.data

# Fetch name from questionnaire
def get_name_by_email(email):
    response = supabase.from_("questionnaire").select("name").eq("email", email).execute()
    if response.error or not response.data:
        return "Unknown User"
    return response.data[0]['name']

@app.route('/')
def home():
    email = request.args.get('email')  # Get email from request parameter
    if not email:
        return "Email not provided!", 400  # Error handling if email isn't provided

    user_groups = get_user_groups(email)
    return render_template('chatgroup.html', groups=user_groups, email=email)

@app.route('/chat/<group_name>')
def chat(group_name):
    email = request.args.get('email')  # Pass email to chat page
    if not email:
        return redirect(url_for('home'))

    return render_template('chat.html', group_name=group_name, email=email)

# Socket.IO event for new message
@socketio.on('new_message')
def handle_new_message(data):
    group_name = data['group_name']
    email = data['email']
    message = data['message']
    
    # Store the message in SQLite
    c.execute("INSERT INTO messages (group_name, email, message) VALUES (?, ?, ?)",
              (group_name, email, message))
    conn.commit()

    # Retrieve the user's name to display
    user_name = get_name_by_email(email)
    data['user_name'] = user_name

    # Broadcast the message to the group
    emit('receive_message', data, room=group_name)

# Join the group room
@socketio.on('join')
def handle_join(data):
    join_room(data['group_name'])
    emit('status', {'msg': f"{data['email']} has entered the chat"}, room=data['group_name'])

if __name__ == '__main__':
    socketio.run(app)
