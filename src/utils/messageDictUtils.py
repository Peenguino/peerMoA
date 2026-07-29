def get_message_dict_template():
    
    messageDict = {
        "id": 0,
        "originalPrompt": "",
        "expectedAnswer": "",
        "generatedText": "",
        "predictedAnswer": "",
        "layerPredictions": [],
        "count": 0,
        "start_time": 0
    }

    return messageDict

def get_message_dict_template_pull():

    messageDict = {
        "id": 0,
        "originalPrompt": "",
        "expectedAnswer": "",
        # This array will contain the 0 to 3 strings produced by the ElabMidService.
        "elaborations": [],
        # Stores the final synthesized character (A, B, C, or D) computed by SynthOutService
        "predictedAnswer": "",
        # Tracks the number of elaborations completed to route the message properly
        "count": 0,
        # Timestamp for End-to-End latency measurement
        "start_time": 0.0,
        # Total len of dataset, used by synthOutService without accessing the dataset
        "total_expected": 0
    }

    return messageDict   