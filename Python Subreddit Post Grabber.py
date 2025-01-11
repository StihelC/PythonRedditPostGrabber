import tkinter as tk
from tkinter import ttk, messagebox
import praw
import os
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from instagrapi import Client
import threading
import json
import time

class RedditInstagramApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit to Instagram Post Generator")
        self.root.geometry("800x600")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='CISSP_Studier',
        )
        
        # Initialize variables
        self.processing = False
        self.instagram_client = None
        
        self.create_gui()
        
    def create_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Reddit Settings
        ttk.Label(main_frame, text="Reddit Settings", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(main_frame, text="Subreddit:").grid(row=1, column=0, sticky=tk.W)
        self.subreddit_var = tk.StringVar(value="minecraft")
        ttk.Entry(main_frame, textvariable=self.subreddit_var).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Number of Posts:").grid(row=2, column=0, sticky=tk.W)
        self.post_limit_var = tk.StringVar(value="3")
        ttk.Entry(main_frame, textvariable=self.post_limit_var).grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Time Filter:").grid(row=3, column=0, sticky=tk.W)
        self.time_filter_var = tk.StringVar(value="day")
        time_filter_combo = ttk.Combobox(main_frame, textvariable=self.time_filter_var)
        time_filter_combo['values'] = ('day', 'week', 'month', 'year', 'all')
        time_filter_combo.grid(row=3, column=1, sticky=(tk.W, tk.E))
        
        # Instagram Settings
        ttk.Label(main_frame, text="Instagram Settings", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Label(main_frame, text="Username:").grid(row=5, column=0, sticky=tk.W)
        self.instagram_username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.instagram_username_var).grid(row=5, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Password:").grid(row=6, column=0, sticky=tk.W)
        self.instagram_password_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.instagram_password_var, show="*").grid(row=6, column=1, sticky=(tk.W, tk.E))
        
        # Auto Upload Settings
        self.auto_upload_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Auto Upload to Instagram", variable=self.auto_upload_var).grid(row=7, column=0, columnspan=2, pady=5)
        
        ttk.Label(main_frame, text="Upload Delay (seconds):").grid(row=8, column=0, sticky=tk.W)
        self.upload_delay_var = tk.StringVar(value="5")
        ttk.Entry(main_frame, textvariable=self.upload_delay_var).grid(row=8, column=1, sticky=(tk.W, tk.E))
        
        # Process Button
        self.process_button = ttk.Button(main_frame, text="Generate Posts", command=self.start_processing)
        self.process_button.grid(row=9, column=0, columnspan=2, pady=20)
        
        # Results Area
        ttk.Label(main_frame, text="Results", font=('Helvetica', 12, 'bold')).grid(row=10, column=0, columnspan=2, pady=10)
        
        self.results_text = tk.Text(main_frame, height=10, width=60)
        self.results_text.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress_bar.grid(row=12, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
        
    def log_message(self, message):
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
        
    def fetch_reddit_posts(self):
        subreddit = self.reddit.subreddit(self.subreddit_var.get())
        posts_with_images = []
        post_limit = int(self.post_limit_var.get())
        
        self.log_message(f"Fetching posts from r/{self.subreddit_var.get()}...")
        
        for post in subreddit.top(time_filter=self.time_filter_var.get(), limit=20):
            if post.url.endswith(('jpg', 'jpeg', 'png', 'gif')) and len(posts_with_images) < post_limit:
                posts_with_images.append({
                    'title': post.title,
                    'url': post.url,
                    'image_url': post.url,
                    'score': post.score,
                    'author': str(post.author),
                    'comments': post.num_comments,
                    'created_utc': post.created_utc
                })
                
                if len(posts_with_images) == post_limit:
                    break
                    
        return posts_with_images
        
    def save_post(self, post_data):
        timestamp = datetime.fromtimestamp(post_data['created_utc']).strftime('%Y%m%d_%H%M%S')
        base_path = r"C:\Users\catas\Desktop\grabber\Pics"
        post_dir = os.path.join(base_path, f"post_{timestamp}")
        os.makedirs(post_dir, exist_ok=True)
        
        # Save post details
        details_path = os.path.join(post_dir, "post_details.txt")
        with open(details_path, 'w') as file:
            file.write(f"Title: {post_data['title']}\n")
            file.write(f"URL: {post_data['url']}\n")
            file.write(f"Score: {post_data['score']}\n")
            file.write(f"Author: {post_data['author']}\n")
            file.write(f"Comments: {post_data['comments']}\n")
        
        # Save image
        image_response = requests.get(post_data['image_url'], stream=True)
        if image_response.status_code == 200:
            image_extension = post_data['image_url'].split('.')[-1].lower()
            if image_extension not in ['jpg', 'jpeg', 'png', 'gif']:
                image_extension = 'jpg'
            original_image_path = os.path.join(post_dir, f"original_image.{image_extension}")
            with open(original_image_path, 'wb') as image_file:
                for chunk in image_response.iter_content(1024):
                    image_file.write(chunk)
            
            # Create Instagram version
            instagram_image_path = os.path.join(post_dir, f"instagram_ready_{timestamp}.jpg")
            self.create_instagram_image(original_image_path, instagram_image_path, post_data['author'])
            
            # Generate caption
            caption_path = os.path.join(post_dir, "instagram_caption.txt")
            self.generate_instagram_caption(post_data, caption_path)
            
            return {
                'post_dir': post_dir,
                'image_path': instagram_image_path,
                'caption_path': caption_path
            }
        return None
        
    def create_instagram_image(self, input_path, output_path, author):
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            # Calculate dimensions
            original_width, original_height = img.size
            aspect_ratio = original_width / original_height
            
            if aspect_ratio > 1:  # Landscape
                new_width = 1080
                new_height = int(1080 / aspect_ratio)
            else:  # Portrait or square
                new_height = 1080
                new_width = int(1080 * aspect_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create canvas
            canvas = Image.new('RGB', (1080, 1080), (0, 0, 0))
            paste_x = (1080 - new_width) // 2
            paste_y = (1080 - new_height) // 2
            canvas.paste(img, (paste_x, paste_y))
            
            # Add caption
            draw = ImageDraw.Draw(canvas)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except IOError:
                font = ImageFont.load_default()
            
            caption = f"Image by: u/{author}"
            text_width = draw.textlength(caption, font=font)
            text_height = 36  # Approximate font height
            
            # Add semi-transparent box
            padding = 10
            box_position = (0, 1080 - text_height - 2 * padding)
            draw.rectangle(
                [box_position, (1080, 1080)],
                fill=(0, 0, 0, 128)
            )
            
            # Add text
            draw.text(
                (padding, 1080 - text_height - padding),
                caption,
                fill=(255, 255, 255),
                font=font
            )
            
            canvas.save(output_path)
            
    def generate_instagram_caption(self, post_data, caption_path):
        caption = f"📌 {post_data['title']}\n\n"
        caption += f"👤 Original post by u/{post_data['author']} on Reddit\n"
        caption += f"💫 {post_data['score']} upvotes • {post_data['comments']} comments\n\n"
        
        # Add hashtags
        hashtags = [
            "#Reddit", "#RedditCommunity", "#Minecraft", "#Gaming",
            "#MinecraftBuild", "#GamerLife", "#GamersOfInstagram",
            "#MinecraftCommunity", "#MinecraftCreative"
        ]
        
        caption += " ".join(hashtags)
        
        with open(caption_path, 'w', encoding='utf-8') as f:
            f.write(caption)
            
    def upload_to_instagram(self, image_path, caption_path):
        try:
            if not self.instagram_client:
                self.instagram_client = Client()
                self.instagram_client.login(
                    self.instagram_username_var.get(),
                    self.instagram_password_var.get()
                )
            
            with open(caption_path, 'r', encoding='utf-8') as f:
                caption = f.read()
            
            media = self.instagram_client.photo_upload(
                image_path,
                caption=caption
            )
            
            return True
        except Exception as e:
            self.log_message(f"Instagram upload failed: {str(e)}")
            return False
            
    def start_processing(self):
        if self.processing:
            return
            
        self.processing = True
        self.process_button.configure(state='disabled')
        self.progress_var.set(0)
        self.results_text.delete(1.0, tk.END)
        
        def process():
            try:
                # Fetch posts
                posts = self.fetch_reddit_posts()
                total_posts = len(posts)
                
                if not posts:
                    self.log_message("No posts with images found!")
                    return
                
                # Process each post
                for i, post in enumerate(posts):
                    self.log_message(f"\nProcessing post {i+1}/{total_posts}: {post['title']}")
                    
                    # Save and process post
                    result = self.save_post(post)
                    if result:
                        self.log_message(f"Post processed and saved to: {result['post_dir']}")
                        
                        # Handle auto upload
                        if self.auto_upload_var.get():
                            self.log_message("Uploading to Instagram...")
                            if self.upload_to_instagram(result['image_path'], result['caption_path']):
                                self.log_message("Upload successful!")
                            else:
                                self.log_message("Upload failed!")
                            
                            # Wait for specified delay
                            time.sleep(int(self.upload_delay_var.get()))
                    
                    self.update_progress((i + 1) * 100 / total_posts)
                
                self.log_message("\nAll posts processed!")
                
            except Exception as e:
                self.log_message(f"An error occurred: {str(e)}")
            finally:
                self.processing = False
                self.process_button.configure(state='normal')
                self.root.update_idletasks()
        
        # Start processing in a separate thread
        threading.Thread(target=process, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditInstagramApp(root)
    root.mainloop()