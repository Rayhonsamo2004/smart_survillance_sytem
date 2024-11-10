Intelligence Survillence System

Sequence diagram:
![image](https://github.com/user-attachments/assets/7475ae89-61b2-48b4-8496-0f5a6fa13fa4)


System Workflow:
	The system begins with CCTV camera sending the request to the cloud so that it is  allocated to one of fog nodes.
	The cloud accepts the proposal from the device and the Deferred acceptance algorithm is deployed in the cloud.
	The cloud uses DAA algorithm to allocate to one of fog nodes. The DAA algorithm works by sending proposal to most preferred fog node based on factors like location, proximity and network quality. the fog nodes accepts the proposal based on factors like capacity or else reject the proposal. if rejected then again send the proposal to next preferred fog node and process continues till the device is allocated to one of fog node.
	"The system starts by using CCTV cameras that capture human activity frame by frame."
	"The captured frames are sent to a nearby fog node which is a Raspberry Pi, where the data is processed locally."
	Advantages:
	Using Raspberry Pi as a fog node reduces the latency issues in processing the data in the cloud. 
	Reduces the workload of the cloud.
	Reduces the overwhelming of resources of cloud if multiple devices send the videos at same time. 
	More sensitive video doesn’t leave the home network if processed locally.
Algorithm for Anomaly Detection:
	"We implemented the CNN algorithm in fog node to analyze these frames and identify any anomalies or suspicious behaviors, such as unusual movements or gathering patterns."
	"Upon detecting an anomaly, the fog node sends an immediate alert to the cloud(AWS)." the cloud retrieves the user details from dynamodb and sends a notification to the user by Simple notification Service.
"The aws dynamodb is used to store the user data and sends notifications by SNS(simple notification service) to the relevant authorities or personnel about the detected abnormal activity."

 
