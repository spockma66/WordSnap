English | [中文](README.md) 

# Project Origin

As a guy who found rote memorization painful, I have always hoped to learn English vocabulary and more authentic expressions through games and watching shows, immersing myself in the context. However, I encountered two problems, using games as an example:

1. This is the first dialogue screen after the actual start of the game **"Warhammer 40,000: Rogue Trader"** (hereinafter referred to as Rogue Trader):

   ![](https://i.imgur.com/i6tD7Be.jpeg)

   For me, there are eight unfamiliar words in this screen of text, making it hard to look them up and disrupting the pace of following the storyline.

2. When looking up words, dictionaries offer several similar explanations. To understand the entire passage, I need to precisely grasp the specific meaning of each of the eight words above while making appropriate inferences, which is quite exhausting.

Therefore, I developed this project to recognize content using a Raspberry Pi. By clicking on words, you can see context-based explanations and hear their pronunciations. Now I'm open-sourcing it, hoping to help others with similar needs.

:red_circle: _**The following demonstration is based on Chinese. But you can use it in YOUR OWN language be modifying 3 items in the configuration file. You can see the instruction in the "Brief Introduction of Configuration Files" section.**_

# Usage Scenarios

- **Recognizing Text on TV**
  - **Game "Rogue Trader"**: See below for the usage of the first dialogue screen in the game. The lower part is a 10-inch touch screen output by the Raspberry Pi:

    ![](https://i.imgur.com/81S39ES.jpeg)

    Touch screen screenshot; the upper part of the text comes from the recognized game dialogue:

    ![](https://i.imgur.com/MPOc8bm.png)

    - Click any word in the two recognition areas above, and the corresponding area below will display the explanation. Highlighted words are from the GRE and TOEFL vocabulary lists; sources are mentioned in the acknowledgments section.
    - Click the last word in the two explanation areas below to hear the pronunciation of the word you just queried.
    - The Raspberry Pi will continuously recognize the text on the big screen, but any operation on the Raspberry Pi interface will pause the recognition. To recognize new content on the big screen again, click **Resume Image Capture** at the bottom of the interface.

  - **English Books**: Cast your phone screen to read English books; the book content:

    ![](https://i.imgur.com/mYUI8Gb.jpeg)

    On a 15.6-inch screen, the recognized content and the explanation of the word "artifacts":

    ![](https://i.imgur.com/RA9yzlB.png)

    Compared with the query result of "artifacts" in the common dictionary below, the context-based explanation above is closer to the current scene:

    ![](https://i.imgur.com/hCDHpaK.jpeg)

- **Recognizing Text on Computer**
  - **Game "Disco Elysium"**: Initial dialogue:

    ![](https://i.imgur.com/9MMxEZx.jpeg)

    Touch screen screenshot:

    ![](https://i.imgur.com/XXm7Oy4.png)

  - **English Video**: "The Story of Cats":

    ![](https://i.imgur.com/doCOuKV.jpeg)

    Touch screen screenshot:

    ![](https://i.imgur.com/SEwyvSW.png)

# Preparation

The test environment for this project mainly consists of a Raspberry Pi 5 with 8GB RAM and an HD camera (capable of taking 1080P photos).

**Hardware Preparation**

- I have purchased all the hardware from Chinese e-commerce services and converted the prices into U.S. dolloars

- **Flashing the System**: Download the Raspberry Pi Imager from the [official Raspberry Pi website](https://www.raspberrypi.com/software/) and install Raspberry Pi OS on a TF card as instructed. You'll need a TF card costing a few dollars (commonly 64GB) and a card reader costing a few dollars. There are many tutorials available; please search for them.

- **Machine Installation**
  - **Important Components**

    ![](https://i.imgur.com/QPyhtJv.jpeg)

    The image above mainly includes:

    - **Raspberry Pi 5 (8GB)** and case; the Raspberry Pi already has the flashed TF card inserted.
    - **10-inch touch screen**, powered by Raspberry Pi 5, connected via HDMI and USB ports. It's used because it takes up less space on the desktop; a non-touch screen works just as well.
    - **USB wireless keyboard**
    - **USB speaker**

  - **Raspberry Pi 5 and Case**

    ![](https://i.imgur.com/NnXSktl.jpeg)

    Due to increased heat when running large models, I tried a big case this time, and the active cooling fan is more effective. However, it's not mandatory to use it, and it's more expensive than a regular case.

  - **USB Speaker**

    ![](https://i.imgur.com/Rpzwd4P.jpeg)

    Purchased from an e-commerce platform, easy to find, priced at 5 dollars.

  - **HD Camera (capable of taking 1080P images)**

    ![](https://i.imgur.com/1YgFmmX.jpeg)

    Purchased from an e-commerce platform, capable of 16x optical + 4x digital zoom, priced at 32 dollars. You'll need to search carefully as most well-known brands are relatively expensive.

    - **Placement for Recognizing TV**: Suspend it over the seating area using a stand to ensure it doesn't touch other objects for stability:

      ![](https://i.imgur.com/VMwvuqJ.jpeg)

      Viewed from the back, it's directly facing the TV:

      ![](https://i.imgur.com/502fZlb.jpeg)

      The type of stand used in the picture can generally be bought for around 15 dollars on e-commerce platforms. It's a mobile live broadcast stand; just add a universal camera adapter.

    - **Placement for Recognizing Computer**: Place it slightly off to the side of the seating area, at about eye level when sitting, shooting downward:

      ![](https://i.imgur.com/SOyKlQy.jpeg)

      Shooting angle as follows (actual photo taken by the camera):

      ![](https://i.imgur.com/6ERlHdj.jpeg)

- **Update System**: After booting up, first execute `sudo apt update` and `sudo apt upgrade`, or use the system UI's update function.

**Software Preparation**

- **Basic Components**
  - Use the built-in Python 3.11 version of Raspberry Pi OS.
  - Install Ollama:

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

    (You can also check the installation methods on the official website [ollama.com](https://ollama.com)), then download the model locally:

    ```bash
    ollama pull qwen2.5:1.5b
    ```

  - To use the USB camera, you also need to install `fswebcam` and `mplayer`; they will be used in later steps.

    - It's strongly recommended to confirm the device path of the camera before testing. First, execute the `lsusb` command to see the camera name in the USB devices. Then execute `v4l2-ctl --list-devices` to display several device paths corresponding to the camera; just use the first one. Ensure that the `usbcam_path` in the config file matches the actual device path found.

    - Install `mplayer`:

      ```bash
      sudo apt install mplayer -y
      ```

      Then test. If the device is `/dev/video0`, execute:

      ```bash
      sudo mplayer tv://
      ```

      Otherwise, add the parameter `"-tv device=your_device_path"` when running.

    - Install `fswebcam`:

      ```bash
      sudo apt install fswebcam -y
      ```

      Then test. If the device is `/dev/video0`, execute:

      ```bash
      fswebcam --no-banner -r 1920x1080 ~/test.jpg
      ```

      Otherwise, add the parameter `"-d your_device_path"` when running.

- **Install the Project Directly (Raspberry Pi OS has Git by default)**

  - **Operation Process**

    ```bash
    git clone https://github.com/spockma66/WordSnap.git
    cd WordSnap
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

  - The project files include ONNX and executable files for direct operation. If you wish to generate them yourself or use other versions, you can delete all files under the `models` directory, and then:

    - Visit RapidAI's [PaddleOCRModelConvert](https://github.com/RapidAI/PaddleOCRModelConvert) to generate your own OCR model for recognizing English, and replace the `ocr_model_path` in the config file.

    - Visit the Kaldi speech framework's [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx), download the base model and voice model, arrange their storage locations, then modify the values in `tts_config`. This part can refer to [this video on Bilibili](https://www.bilibili.com/video/BV1tu4y1H7jD/). If you want to change the speech effect during use, please also refer to that video.

# Getting Started

- First, change the `current_mode` value in the config file to `test` and save it. Then execute `python main.py` in the virtual environment to see the effect of the captured photos, including:

  - Aiming at and properly aligning the recognition target.
  - Clear focus.
  - Recognized all the text that should be recognized; you can see which text is covered by the bounding boxes.
  - Whether it recognized fixed text that doesn't need to be recognized. For example, the brand name displayed at the bottom edge of the TV can interfere with text classification results. These fixed texts can be excluded using `black_list` in the config. I used a Redmi TV, so my `black_list` value is `["Redmi"]`.

- If you find any issues, you can reopen `mplayer` to adjust position, focus, and brightness. Please note that the effect displayed by `mplayer` may be inconsistent with the photos taken in test mode, but you can still zoom in and out and adjust brightness. Eventully, please make sure the effect of the photos taken in test mode is good.

- When finishing adjustments, make sure the camera is placed somewhere it won't easily shake to ensure stable photo taking. Then change the `current_mode` value in the config file to `normal` and save.

- In the virtual environment, execute `python main.py` to start using.

# Brief Introduction of Configuration Files

- The configuration files are located in the `configs` folder under the project directory; there are three in total. The names of the configuration items are relatively self-explanatory. You can check them yourself first; a brief introduction is as follows:

- **`config` File**: Includes configurations related to starting and recognizing text, organizing into paragraphs, and displaying. If the user speaks a language other than Chinese, modifying three configuration items for use:

  - In `ollama_api`, under `data`, change the `model` to one that performs better in your language, or a relatively general model like `llama3.2:1b`. A 3B model will also work but might be a bit slow. And before using it in the program, download it by running `ollama pull llama3.2:1b` to save time for the first usage.

  - In `ollama_api`, under `data`, modify the `prompt` to your language, instructing the model to explain the meaning of the word in context(mentioned as full_text) and its common usage. However, the format of `{word}` and `{full_text}` must not be changed.

  - `pronunciation_hint`: Change it to your language to prompt the user that clicking the word will play its pronunciation.

- **`ui_config` File**: Includes configurations related to the user interface.

- **`tts_config` File**: Configurations related to the startup of the pronunciation model and speech speed.

  Detailed instructions will be added later.

  After modifying and saving the configuration files, please restart the program.

# FAQ

- **How do I use this product?** Get the program started by follwing the instructions above, and then focus on the content on the big screen first. After identifying unfamiliar words, check the recognition results from the Raspberry Pi and click on specific words to query. Any operation on the Raspberry Pi interface will pause the continuous recognition of the big screen, ensuring that the currently focused content is not refreshed. Click **Resume Image Capture** at the bottom to continue recognizing new content.

- **What if the focus looks clear when adjusting the camera, but the recognized results still have flaws (e.g., spaces between words are not recognized)?** You can open the camera with `mplayer`, then use the remote control to lower the camera's brightness. As long as the words look clearer, don't worry about the brightness of the captured image. This operation is particularly effective when the screen being captured is illuminated by external strong light sources (ceiling lights or desk lamps).

- **Can a 720p USB camera be used?** Not recommended; my experience with it was not satisfactory.

- **Can the official Raspberry Pi camera be used?** At least the 3rd generation can be used; it performs better when capturing TV screens, as shown below. However, it's challenging to capture computer screens due to the short and inflexible CSI flat cable, so the actual effect cannot be verified.

  - **Usage Effect**

    ![](https://i.imgur.com/NyJowsO.jpeg)

  - **Camera Placement**: The camera is the official Camera Module 3 Wide (40 dollars), and the connection cable is a 50 cm CSI camera cable (4 dollars):

    ![](https://i.imgur.com/jNvWZHi.jpeg)

  - **Shooting Angle**: Obtained photos through test mode; recognized text is within the boxes:

    ![](https://i.imgur.com/fmgV7lQ.png)

  - **Final Recognition Result Screenshot**

    ![](https://i.imgur.com/k3s16PI.png)

- **Is the recognition effective in all game scenes?** For game interfaces with significant animations, strong contrast in font brightness, or many decorative fonts—such as the main menu when first entering a game—the recognition effect may be slightly less accurate.

- **Why is there a slight pause after the prompt tone when listening to pronunciations, followed by a sentence, instead of directly pronouncing the word like common dictionaries?** After multiple attempts, I chose a medium version of the pronunciation, which takes longer. If the word is pronounced directly, the probability of incorrect stress increases, possibly related to the distribution of training materials.

- **Will it secretly send back data or photos taken?** No. If you're concerned and don't want to check the code, you can use the Raspberry Pi after disconnecting it from the network (ensure you've installed the project first), and reconnect after closing the program.

- **If issues are found, what information can be referenced?** Serious camera issues will be indicated on the interface. In the `log` folder under the local project directory, logs from the last run are stored. You can open them if interested and study them along with the code.

# Acknowledgments

1. The OCR recognition feature is made possible by [RapidAI](https://github.com/RapidAI/) and [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR).

2. The default word explanation feature is made possible by [Qwen2.5](https://github.com/QwenLM/Qwen2.5) from Tongyi Qianwen and [Ollama](https://ollama.com/).

3. The default word pronunciation feature is made possible by [Kaldi Speech Framework](https://github.com/k2-fsa/sherpa-onnx) and [Piper](https://github.com/rhasspy/piper).

4. The default highlighted word vocabulary is from [mahavivo's vocabulary list](https://github.com/mahavivo/vocabulary/tree/master/vocabulary).

