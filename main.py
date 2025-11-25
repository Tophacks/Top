import tkinter as tk
from tkinter import font
import cv2
from PIL import Image, ImageTk
import threading
import winsound

import tkinter as tk
from tkinter import font
import cv2
from PIL import Image, ImageTk
import threading
import winsound
import queue

class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.configure(bg="#2c3e50")

        # Initialize HOG descriptor for person detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # Title Label
        self.title_label = tk.Label(window, text="Security Camera", font=("Helvetica", 20, "bold"), bg="#2c3e50", fg="white")
        self.title_label.pack(pady=10)

        # Video Canvas with a frame
        self.canvas_frame = tk.Frame(window, bg="black", borderwidth=2, relief="solid")
        self.canvas_frame.pack(pady=10, padx=10)
        self.canvas = tk.Canvas(self.canvas_frame, width=640, height=480, bg="black")
        self.canvas.pack()

        # Controls Frame
        self.controls_frame = tk.Frame(window, bg="#34495e")
        self.controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Status Label
        self.status_label = tk.Label(self.controls_frame, text="Status: Idle", font=("Helvetica", 12), bg="#34495e", fg="white")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Buttons
        self.btn_start = tk.Button(self.controls_frame, text="Start Camera", width=15, command=self.start_camera, bg="#2ecc71", fg="white", activebackground="#27ae60", relief="flat")
        self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop = tk.Button(self.controls_frame, text="Stop Camera", width=15, command=self.stop_camera, state=tk.DISABLED, bg="#e74c3c", fg="white", activebackground="#c0392b", relief="flat")
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_quit = tk.Button(self.controls_frame, text="Quit", width=15, command=self.quit)
        self.btn_quit.pack(side=tk.RIGHT, padx=5, pady=5)

        self.is_camera_running = False
        self.producer_thread = None
        self.consumer_thread = None
        self.queue = queue.Queue(maxsize=5)
        
        self.window.mainloop()

    def start_camera(self):
        self.is_camera_running = True
        self.producer_thread = threading.Thread(target=self.frame_producer)
        self.producer_thread.start()
        self.consumer_thread = threading.Thread(target=self.video_loop)
        self.consumer_thread.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

    def frame_producer(self):
        vid = cv2.VideoCapture(0)
        while self.is_camera_running and vid.isOpened():
            ret, frame = vid.read()
            if ret:
                try:
                    self.queue.put(frame, block=False)
                except queue.Full:
                    # if the queue is full, just drop the frame
                    pass
            else:
                break
        vid.release()

    def stop_camera(self):
        self.is_camera_running = False
        # Wait for threads to finish
        if self.producer_thread and self.producer_thread.is_alive():
            self.producer_thread.join()
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join()
            
        # Clear the queue
        while not self.queue.empty():
            self.queue.get_nowait()

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.canvas.delete("all")
        self.status_label.config(text="Status: Idle", fg="white")

    def video_loop(self):
        frame_count = 0
        while self.is_camera_running:
            try:
                frame = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            frame_count += 1
            motion_detected = False
            
            # Process every 3rd frame
            if frame_count % 3 == 0:
                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (400, int(400 * frame.shape[0] / frame.shape[1])))
                processed_frame, motion_detected = self.motion_detection(small_frame)
                # Resize back to original size for display
                processed_frame = cv2.resize(processed_frame, (frame.shape[1], frame.shape[0]))
            else:
                processed_frame = frame

            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(processed_frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

            if motion_detected:
                self.status_label.config(text="Status: Person Detected!", fg="#e74c3c")
                winsound.Beep(500, 200)
            else:
                # Only update the status if it's not already "No Person Detected"
                if self.status_label.cget("text") != "Status: No Person Detected":
                    self.status_label.config(text="Status: No Person Detected", fg="#2ecc71")
    
    def motion_detection(self, frame):
        motion_detected = False
        # detect people in the image
        (rects, weights) = self.hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.05)
        
        for (x, y, w, h) in rects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            motion_detected = True
        
        return frame, motion_detected

    def quit(self):
        self.stop_camera()
        self.window.quit()

    def __del__(self):
        if self.is_camera_running:
            self.stop_camera()




if __name__ == '__main__':
    App(tk.Tk(), "Tkinter and OpenCV")
