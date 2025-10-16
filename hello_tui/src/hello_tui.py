import os
import time
import sys
from datetime import datetime

def clear_screen():
    """Clear the command line screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    """Display the application header"""
    print("=" * 50)
    print("           HELLO TUI APPLICATION")
    print("=" * 50)
    print()

def display_menu():
    """Display the main menu"""
    print("📋 MAIN MENU")
    print("1. Display Hello Message")
    print("2. Show Current Time")
    print("3. System Information")
    print("4. Exit")
    print()

def get_choice():
    """Get user choice with validation"""
    try:
        choice = input("Enter your choice (1-4): ").strip()
        return choice
    except KeyboardInterrupt:
        return '4'

def hello_message():
    """Display hello message"""
    clear_screen()
    display_header()
    print("✨ HELLO FROM TUI WORLD! ✨")
    print()
    print("This is a command line Text User Interface.")
    print("You can navigate using keyboard inputs.")
    print()
    input("Press Enter to continue...")

def show_time():
    """Display current time"""
    clear_screen()
    display_header()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕒 CURRENT TIME: {current_time}")
    print()
    input("Press Enter to continue...")

def system_info():
    """Display system information"""
    clear_screen()
    display_header()
    print("💻 SYSTEM INFORMATION")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Current Directory: {os.getcwd()}")
    print()
    input("Press Enter to continue...")

def exit_app():
    """Exit the application"""
    clear_screen()
    print("=" * 50)
    print("    Thank you for using Hello TUI! 👋")
    print("=" * 50)
    time.sleep(2)
    clear_screen()

def main():
    """Main application loop"""
    while True:
        clear_screen()
        display_header()
        display_menu()
        
        choice = get_choice()
        
        if choice == '1':
            hello_message()
        elif choice == '2':
            show_time()
        elif choice == '3':
            system_info()
        elif choice == '4':
            exit_app()
            break
        else:
            print()
            print("❌ Invalid choice! Please enter 1-4.")
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Goodbye! 👋")
        time.sleep(2)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        input("Press Enter to exit...")