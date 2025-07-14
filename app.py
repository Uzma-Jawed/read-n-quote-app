import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import uuid
from typing import Dict, List, Optional, Tuple

# Constants
DATA_DIR = "data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
QUOTES_FILE = os.path.join(DATA_DIR, "quotes.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BANNER_IMAGE = "banner.png"
PROFILE_IMAGE = "profilepic.png"

# Ensure data directory exists
Path(DATA_DIR).mkdir(exist_ok=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Load data functions
def load_data(filename: str) -> Dict:
    """Load JSON data from file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data: Dict, filename: str) -> None:
    """Save data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize data files if they don't exist
for file in [BOOKS_FILE, QUOTES_FILE, USERS_FILE]:
    if not os.path.exists(file):
        save_data({}, file)

# User authentication functions
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register a new user."""
    users = load_data(USERS_FILE)
    if username.strip() == "":
        return False, "Username cannot be empty"
    if password.strip() == "":
        return False, "Password cannot be empty"
    if username in users:
        return False, "Username already exists"
    
    users[username] = {"password": password}
    save_data(users, USERS_FILE)
    
    # Initialize user's books and quotes
    books_data = load_data(BOOKS_FILE)
    books_data[username] = {"books": {}}
    save_data(books_data, BOOKS_FILE)
    
    quotes_data = load_data(QUOTES_FILE)
    quotes_data[username] = {"quotes": {}}
    save_data(quotes_data, QUOTES_FILE)
    
    return True, "Registration successful"

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate a user."""
    users = load_data(USERS_FILE)
    if username not in users:
        return False, "Username not found"
    if users[username]["password"] != password:
        return False, "Incorrect password"
    
    st.session_state.authenticated = True
    st.session_state.current_user = username
    return True, "Login successful"

def logout_user() -> None:
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_page = "Home"

# Book management functions
def add_book(username: str, book_data: Dict) -> None:
    """Add a new book for the user."""
    books_data = load_data(BOOKS_FILE)
    book_id = str(uuid.uuid4())
    book_data['entry_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    book_data['last_updated'] = book_data['entry_date']
    books_data[username]['books'][book_id] = book_data
    save_data(books_data, BOOKS_FILE)
    st.balloons()

def get_books(username: str) -> Dict:
    """Get all books for a user."""
    books_data = load_data(BOOKS_FILE)
    return books_data.get(username, {}).get('books', {})

def update_book(username: str, book_id: str, updates: Dict) -> bool:
    """Update a book's information."""
    books_data = load_data(BOOKS_FILE)
    if username in books_data and book_id in books_data[username]['books']:
        books_data[username]['books'][book_id].update(updates)
        books_data[username]['books'][book_id]['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(books_data, BOOKS_FILE)
        return True
    return False

def delete_book(username: str, book_id: str) -> bool:
    """Delete a book."""
    books_data = load_data(BOOKS_FILE)
    if username in books_data and book_id in books_data[username]['books']:
        del books_data[username]['books'][book_id]
        save_data(books_data, BOOKS_FILE)
        
        # Also delete any quotes associated with this book
        quotes_data = load_data(QUOTES_FILE)
        if username in quotes_data:
            quotes_to_delete = [
                qid for qid, quote in quotes_data[username]['quotes'].items() 
                if quote.get('book_id') == book_id
            ]
            for qid in quotes_to_delete:
                del quotes_data[username]['quotes'][qid]
            save_data(quotes_data, QUOTES_FILE)
        
        return True
    return False

# Quote management functions
def add_quote(username: str, quote_data: Dict) -> None:
    """Add a new quote for the user."""
    quotes_data = load_data(QUOTES_FILE)
    quote_id = str(uuid.uuid4())
    quote_data['entry_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if username not in quotes_data:
        quotes_data[username] = {"quotes": {}}
    
    quotes_data[username]['quotes'][quote_id] = quote_data
    save_data(quotes_data, QUOTES_FILE)
    st.balloons()

def get_quotes(username: str) -> Dict:
    """Get all quotes for a user."""
    quotes_data = load_data(QUOTES_FILE)
    return quotes_data.get(username, {}).get('quotes', {})

def delete_quote(username: str, quote_id: str) -> bool:
    """Delete a quote."""
    quotes_data = load_data(QUOTES_FILE)
    if username in quotes_data and quote_id in quotes_data[username]['quotes']:
        del quotes_data[username]['quotes'][quote_id]
        save_data(quotes_data, QUOTES_FILE)
        return True
    return False

# Analysis functions
def books_completed_in_year(username: str, year: int) -> Dict:
    """Get books completed in a specific year."""
    books = get_books(username)
    return {
        k: v for k, v in books.items() 
        if v.get('status', '').lower() == 'completed' 
        and str(year) in v.get('year', '')
    }

def book_with_most_quotes(username: str) -> Optional[Tuple[str, int]]:
    """Get the book with the most quotes."""
    quotes = get_quotes(username)
    book_counts = {}
    
    for quote in quotes.values():
        book_title = quote.get('book_title', 'Unknown Book')
        book_counts[book_title] = book_counts.get(book_title, 0) + 1
    
    return max(book_counts.items(), key=lambda x: x[1]) if book_counts else None

def author_with_most_books(username: str) -> Optional[Tuple[str, int]]:
    """Get the author with the most books."""
    books = get_books(username)
    author_counts = {}
    
    for book in books.values():
        author = book.get('author', 'Unknown Author')
        author_counts[author] = author_counts.get(author, 0) + 1
    
    return max(author_counts.items(), key=lambda x: x[1]) if author_counts else None

def get_reading_stats(username: str) -> Dict:
    """Get various reading statistics for the user."""
    books = get_books(username)
    quotes = get_quotes(username)
    
    stats = {
        'total_books': len(books),
        'total_quotes': len(quotes),
        'books_by_status': {},
        'genres': {}
    }
    
    # Count books by status
    for book in books.values():
        status = book.get('status', 'Unknown')
        stats['books_by_status'][status] = stats['books_by_status'].get(status, 0) + 1
        
        # Count genres
        for genre in book.get('genres', []):
            stats['genres'][genre] = stats['genres'].get(genre, 0) + 1
    
    # Get most recent books
    sorted_books = sorted(
        books.items(), 
        key=lambda x: x[1].get('entry_date', ''), 
        reverse=True
    )
    stats['recent_books'] = sorted_books[:3]
    
    return stats

# UI Components
def show_home() -> None:
    """Display the home page."""
    st.image(BANNER_IMAGE, use_container_width=True)
    st.title("Personal Reading Journal & Quote Collector")
    st.markdown("""
    Welcome to your personal reading journal! This app helps you:
    - Log all the books you read
    - Collect your favorite quotes
    - Analyze your reading habits
    """)
    
    if st.session_state.authenticated:
        st.subheader("Your Reading Stats")
        stats = get_reading_stats(st.session_state.current_user)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Books", stats['total_books'])
        with col2:
            st.metric("Total Quotes", stats['total_quotes'])
        with col3:
            completed = stats['books_by_status'].get('Completed', 0)
            st.metric("Books Completed", completed)
        
        if stats['recent_books']:
            st.subheader("Recently Added Books")
            for book_id, book in stats['recent_books']:
                with st.expander(f"{book.get('title', 'Untitled')} by {book.get('author', 'Unknown')}"):
                    st.write(f"Status: {book.get('status', 'Unknown')}")
                    st.write(f"Added on: {book.get('entry_date', 'Unknown').split()[0]}")

def show_auth() -> None:
    """Display authentication forms."""
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("New Username", key="reg_username")
            new_password = st.text_input("New Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            submitted = st.form_submit_button("Register")
            if submitted:
                if not new_username or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def show_book_management() -> None:
    """Display book management interface."""
    st.header("Book Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Book", "View Books", "Manage Books"])
    
    with tab1:
        with st.form("add_book_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Title*")
                author = st.text_input("Author*")
                year = st.number_input("Year Published", min_value=0, max_value=datetime.now().year)
            with col2:
                genres = st.text_input("Genres (comma separated)")
                status = st.selectbox("Status", ["Want to Read", "Currently Reading", "Completed", "Dropped"])
                rating = st.slider("Rating (1-5)", 1, 5, 3)
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Book"):
                if not title or not author:
                    st.error("Title and Author are required fields")
                else:
                    add_book(st.session_state.current_user, {
                        "title": title,
                        "author": author,
                        "year": str(year) if year else "",
                        "genres": [g.strip() for g in genres.split(",")] if genres else [],
                        "status": status,
                        "rating": rating,
                        "notes": notes
                    })
                    st.success("Book added successfully!")
    
    with tab2:
        books = get_books(st.session_state.current_user)
        if not books:
            st.info("No books added yet.")
        else:
            # Search and filter options
            with st.expander("Search & Filter"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    search_term = st.text_input("Search by title or author")
                with col2:
                    genre_filter = st.text_input("Filter by genre")
                with col3:
                    status_filter = st.selectbox(
                        "Filter by status", 
                        ["All"] + ["Want to Read", "Currently Reading", "Completed", "Dropped"]
                    )
                
                min_rating = st.slider("Minimum rating", 1, 5, 1)
            
            # Sort options
            sort_options = {
                "Title": "title",
                "Author": "author",
                "Year": "year",
                "Rating": "rating",
                "Recently Added": "entry_date"
            }
            sort_by = st.selectbox("Sort by", list(sort_options.keys()))
            reverse_order = st.checkbox("Descending order", value=True if sort_by in ["Rating", "Recently Added"] else False)
            
            # Filter and sort books
            filtered_books = []
            for book_id, book in books.items():
                title_match = not search_term or search_term.lower() in book.get('title', '').lower()
                author_match = not search_term or search_term.lower() in book.get('author', '').lower()
                genre_match = not genre_filter or any(
                    genre_filter.lower() in genre.lower() 
                    for genre in book.get('genres', [])
                )
                status_match = status_filter == "All" or book.get('status', '') == status_filter
                rating_match = book.get('rating', 0) >= min_rating
                
                if (title_match or author_match) and genre_match and status_match and rating_match:
                    filtered_books.append((book_id, book))
            
            # Sort books
            if sort_by == "Rating":
                filtered_books.sort(
                    key=lambda x: x[1].get('rating', 0), 
                    reverse=reverse_order
                )
            else:
                filtered_books.sort(
                    key=lambda x: x[1].get(sort_options[sort_by], "").lower(), 
                    reverse=reverse_order
                )
            
            if not filtered_books:
                st.info("No books match your filters.")
            else:
                st.write(f"Showing {len(filtered_books)} of {len(books)} books")
                
                for book_id, book in filtered_books:
                    with st.expander(f"{book.get('title', 'Untitled')} by {book.get('author', 'Unknown')}"):
                        cols = st.columns([1, 1, 1, 1])
                        with cols[0]:
                            st.write(f"Year: {book.get('year', 'Unknown')}")
                        with cols[1]:
                            st.write(f"Status: {book.get('status', 'Unknown')}")
                        with cols[2]:
                            rating = book.get('rating', 0)
                            if rating > 0:
                                st.write(f"Rating: {'⭐' * rating}")
                        with cols[3]:
                            st.write(f"Added: {book.get('entry_date', 'Unknown').split()[0]}")
                        
                        st.write(f"Genres: {', '.join(book.get('genres', []))}")
                        
                        if book.get('notes'):
                            st.write("Notes:")
                            st.write(book['notes'])
    
    with tab3:
        books = get_books(st.session_state.current_user)
        if not books:
            st.info("No books to manage.")
        else:
            book_options = {
                f"{v['title']} by {v['author']} (ID: {k[-8:]})": k 
                for k, v in books.items()
            }
            selected_book = st.selectbox(
                "Select a book to manage", 
                list(book_options.keys())
            )
            book_id = book_options[selected_book]
            book_data = books[book_id]
            
            st.subheader("Book Details")
            st.write(f"Title: {book_data.get('title', 'Untitled')}")
            st.write(f"Author: {book_data.get('author', 'Unknown')}")
            
            with st.form("update_book_form"):
                st.write("Update Information")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_status = st.selectbox(
                        "Status", 
                        ["Want to Read", "Currently Reading", "Completed", "Dropped"],
                        index=["Want to Read", "Currently Reading", "Completed", "Dropped"].index(
                            book_data.get('status', 'Want to Read')
                        )
                    )
                    new_year = st.text_input(
                        "Year", 
                        value=book_data.get('year', '')
                    )
                with col2:
                    new_rating = st.slider(
                        "Rating", 
                        1, 5, 
                        value=book_data.get('rating', 3)
                    )
                    new_genres = st.text_input(
                        "Genres (comma separated)", 
                        value=", ".join(book_data.get('genres', []))
                    )
                
                new_notes = st.text_area(
                    "Notes", 
                    value=book_data.get('notes', '')
                )
                
                if st.form_submit_button("Update Book"):
                    updates = {
                        "status": new_status,
                        "year": new_year,
                        "genres": [g.strip() for g in new_genres.split(",")] if new_genres else [],
                        "rating": new_rating,
                        "notes": new_notes
                    }
                    if update_book(st.session_state.current_user, book_id, updates):
                        st.success("Book updated successfully!")
                    else:
                        st.error("Failed to update book")
            
            st.subheader("Delete Book")
            st.warning("This will permanently delete the book and all associated quotes.")
            if st.button("Delete Book"):
                if delete_book(st.session_state.current_user, book_id):
                    st.success("Book deleted successfully!")
                else:
                    st.error("Failed to delete book")

def show_quote_management() -> None:
    """Display quote management interface."""
    st.header("Quote Collector")
    
    tab1, tab2, tab3 = st.tabs(["Add Quote", "View Quotes", "Manage Quotes"])
    
    with tab1:
        books = get_books(st.session_state.current_user)
        if not books:
            st.warning("Please add some books first before adding quotes.")
        else:
            book_options = {
                f"{v['title']} by {v['author']}": {
                    "book_title": v['title'],
                    "book_id": k
                } 
                for k, v in books.items()
            }
            
            with st.form("add_quote_form", clear_on_submit=True):
                quote_text = st.text_area("Quote Text*", height=150)
                
                col1, col2 = st.columns(2)
                with col1:
                    selected_book = st.selectbox(
                        "Book", 
                        list(book_options.keys()))
                    book_info = book_options[selected_book]
                with col2:
                    page_number = st.text_input("Page Number (optional)")
                    tags = st.text_input("Tags (comma separated)")
                
                if st.form_submit_button("Add Quote"):
                    if not quote_text:
                        st.error("Quote text is required")
                    else:
                        add_quote(st.session_state.current_user, {
                            "text": quote_text,
                            "book_title": book_info["book_title"],
                            "book_id": book_info["book_id"],
                            "page_number": page_number,
                            "tags": [t.strip() for t in tags.split(",")] if tags else [],
                            "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.success("Quote added successfully!")
    
    with tab2:
        quotes = get_quotes(st.session_state.current_user)
        if not quotes:
            st.info("No quotes added yet.")
        else:
            # Search and filter options
            with st.expander("Search & Filter"):
                search_term = st.text_input("Search quote text")
                book_filter = st.text_input("Filter by book title")
                tag_filter = st.text_input("Filter by tag")
            
            # Sort options
            sort_options = {
                "Book": "book_title",
                "Recently Added": "entry_date",
                "Random": "random"
            }
            sort_by = st.selectbox("Sort by", list(sort_options.keys()))
            
            # Prepare and filter quotes
            quotes_list = []
            for quote_id, quote in quotes.items():
                book_title = quote.get('book_title', 'Unknown Book')
                books = get_books(st.session_state.current_user)
                author = next(
                    (b['author'] for b in books.values() 
                    if b.get('title') == book_title), 
                    'Unknown Author'
                )
                
                text_match = not search_term or search_term.lower() in quote.get('text', '').lower()
                book_match = not book_filter or book_filter.lower() in book_title.lower()
                tag_match = not tag_filter or any(
                    tag_filter.lower() in tag.lower() 
                    for tag in quote.get('tags', [])
                )
                
                if text_match and book_match and tag_match:
                    quotes_list.append({
                        'id': quote_id,
                        'text': quote.get('text', ''),
                        'book_title': book_title,
                        'author': author,
                        'page_number': quote.get('page_number', ''),
                        'tags': quote.get('tags', []),
                        'entry_date': quote.get('entry_date', '')
                    })
            
            # Sort quotes
            if sort_by == "Book":
                quotes_list.sort(key=lambda x: (x['book_title'], x['author']))
            elif sort_by == "Recently Added":
                quotes_list.sort(key=lambda x: x['entry_date'], reverse=True)
            else:  # Random
                import random
                random.shuffle(quotes_list)
            
            if not quotes_list:
                st.info("No quotes match your filters.")
            else:
                st.write(f"Showing {len(quotes_list)} of {len(quotes)} quotes")
                
                for quote in quotes_list:
                    with st.expander(f"From {quote['book_title']} by {quote['author']}"):
                        st.write(quote['text'])
                        
                        cols = st.columns(3)
                        with cols[0]:
                            if quote['page_number']:
                                st.caption(f"Page {quote['page_number']}")
                        with cols[1]:
                            if quote['tags']:
                                st.caption(f"Tags: {', '.join(quote['tags'])}")
                        with cols[2]:
                            st.caption(f"Added: {quote['entry_date'].split()[0]}")
    
    with tab3:
        quotes = get_quotes(st.session_state.current_user)
        if not quotes:
            st.info("No quotes to manage.")
        else:
            # Create a mapping of quote text to quote ID
            quote_options = {}
            for quote_id, quote in quotes.items():
                preview = quote['text'][:50] + "..." if len(quote['text']) > 50 else quote['text']
                quote_options[f"{preview} (from {quote.get('book_title', 'Unknown')})"] = quote_id
            
            selected_quote = st.selectbox(
                "Select a quote to delete", 
                list(quote_options.keys())
            )
            quote_id = quote_options[selected_quote]
            
            st.warning("This action cannot be undone")
            if st.button("Delete Quote"):
                if delete_quote(st.session_state.current_user, quote_id):
                    st.success("Quote deleted successfully!")
                else:
                    st.error("Failed to delete quote")

def show_analysis() -> None:
    """Display reading analysis."""
    st.header("Reading Analysis")
    
    books = get_books(st.session_state.current_user)
    if not books:
        st.info("Add some books to see analysis.")
        return
    
    stats = get_reading_stats(st.session_state.current_user)
    
    # Overall stats
    st.subheader("Your Reading Stats")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Books", stats['total_books'])
    with col2:
        st.metric("Total Quotes", stats['total_quotes'])
    with col3:
        completed = stats['books_by_status'].get('Completed', 0)
        st.metric("Books Completed", completed)
    with col4:
        reading = stats['books_by_status'].get('Currently Reading', 0)
        st.metric("Currently Reading", reading)
    
    # Books by status
    st.subheader("Books by Status")
    if stats['books_by_status']:
        status_data = {
            "Status": list(stats['books_by_status'].keys()),
            "Count": list(stats['books_by_status'].values())
        }
        st.bar_chart(status_data, x="Status", y="Count")
    else:
        st.info("No status data available")
    
    # Books by genre
    st.subheader("Top Genres")
    if stats['genres']:
        sorted_genres = sorted(
            stats['genres'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]  # Show top 10 genres
        
        genre_data = {
            "Genre": [g[0] for g in sorted_genres],
            "Count": [g[1] for g in sorted_genres]
        }
        st.bar_chart(genre_data, x="Genre", y="Count")
    else:
        st.info("No genre data available")
    
    # Yearly completion
    st.subheader("Books Completed by Year")
    year = st.number_input(
        "Enter year", 
        min_value=1900, 
        max_value=datetime.now().year, 
        value=datetime.now().year
    )
    completed_books = books_completed_in_year(st.session_state.current_user, year)
    
    if not completed_books:
        st.info(f"No books completed in {year}")
    else:
        st.write(f"Books completed in {year}:")
        for book_id, book in completed_books.items():
            rating = book.get('rating', 0)
            rating_display = f" ({'⭐' * rating})" if rating > 0 else ""
            st.write(f"- {book['title']} by {book['author']}{rating_display}")
    
    # Most quoted book
    st.subheader("Most Quoted Book")
    result = book_with_most_quotes(st.session_state.current_user)
    if result:
        book_title, count = result
        st.write(f"{book_title} with {count} quotes")
    else:
        st.info("No quotes added yet.")
    
    # Most read author
    st.subheader("Most Read Author")
    result = author_with_most_books(st.session_state.current_user)
    if result:
        author, count = result
        st.write(f"{author} with {count} books")
    else:
        st.info("No author data available")

# Main App
def main() -> None:
    """Main application function."""
    # Sidebar with profile and navigation
    st.sidebar.image(PROFILE_IMAGE, width=100)
    
    if st.session_state.authenticated:
        st.sidebar.title(f"Welcome, {st.session_state.current_user}!")
        if st.sidebar.button("Logout"):
            logout_user()
            return
        
        nav_options = ["Home", "Book Management", "Quote Collector", "Reading Analysis"]
        selection = st.sidebar.radio("Navigation", nav_options)
        
        if selection == "Home":
            show_home()
        elif selection == "Book Management":
            show_book_management()
        elif selection == "Quote Collector":
            show_quote_management()
        elif selection == "Reading Analysis":
            show_analysis()
    else:
        st.sidebar.title("Please login")
        show_auth()
        show_home()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Personal Reading Journal",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    main()