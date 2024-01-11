import sqlite3

def create_database(db_path: str) -> None:
    """
    Create a new SQLite database with a single table called activity_data.
    
    Parameters
    ----------
    db_path : str
        Path to the database file.
        
    Returns
    -------
    None 
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create a new table with activity_name as a unique key
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_data (
            activity_name TEXT UNIQUE,
            people INTEGER,
            technology INTEGER,
            cost INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

def insert_activity_data(db_path: str, activity_name: str, people: int, technology: int, cost: int) -> None:
    """
    Insert or replace a row in the activity_data table.
    
    Parameters
    ----------
    db_path : str
        Path to the database file.
    activity_name : str
        Name of the activity.
    people : int
        Value of the people slider.
    technology : int
        Value of the technology slider.
    cost : int
        Value of the cost slider.
        
    Returns
    -------
    None 
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute(
            'INSERT OR REPLACE INTO activity_data (activity_name, people, technology, cost) VALUES (?, ?, ?, ?)', 
            (activity_name, people, technology, cost)
        )

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f'Database error: {e}')
    except Exception as e:
        print(f'Exception in _query: {e}')