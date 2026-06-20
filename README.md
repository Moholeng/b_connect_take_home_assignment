# b_connect_take_home_assignment

// project overview

Full stack app that simulates integration with a third party Wi-Fi controller API,
My submissiion for the b_connect junior fullstack developer role, a applicaton where we can see the activity and monitor wifi access and activity, Fastapi backend app that is integrated with a third party wifi contoller getting information from the wifi endpoint and exposing it to our frontend react app to show wifi usage most active venues active session, times the wifi is most used and the age and gender that uses the wifi more, This app serves as a dashboard for devs management and stakeholders giving us a clear overview of usage activity, integrating our fastapi backend with thisrd party wifi controllers and creating our own api layer gives us controll over audit logs and session timeout, giving us a clear understanding of how the endpoint are being used and when and why there are faultys so we can fix the quicker and more effectively

// Tech Stack

Python
Fastapi
Https
Httpx
Uvicorn
Supabase
Postgres
React
Tailwind
Vite
Vercel

// Planning process

The plan for this project seems easy in my mind but i know it will take some architecture,firstly getting the data to work with, the options stated are interesting, i can create a json file wit a data payload mimicking how real data for a wifi controller might work but thats not interesting, bumped into a wifi controller api documentation that i can use and call to get the data called https://www.mywifinetworks.com/developers the api endpoint macth the project scope and it also gives me room to practice how it feels like to work and integrate with a real wifi controller endpoint, after i have the enpoint data using python build in https module, I will the use my FastApi application and create our api layer and wrap the api data from mywifinetwork into our own api endpoints, wrapping a third part api into our own api endpoint seems redundant but it gives us a clear understanding of our data and logs,uvicorn server runing on port 8000 to expose the api endpoint to our frontend to retrieve the data and create a real tmie interactive dashboard, supabase pstgress data base for data capturing and audit logs have 2 tables user_information to staore users info login start and end time gender mac_address for uuid and audit_logs for devs telling us which endpoint was triggered thhe httpx status so we know if the call was a success or error from which device and path, simple react frontend with two toggles management and devs, management page shows the data from the user_information table giving a clear understanding of client data and wifi controller activity read only, add an ai agent using openai sdk that management can text in plain englis and it then queries the database with any information, dev page has all the data from the audit_log table giving devs a  backend understanding of the app what errors we facing have a soc analyst agent that analysis the logs for any errors and pings devs upoan any failed api log,

// Goal 
My goal is to complete this project and to end and that will be able to be done with the help of AI i will be using gemini pro for planning, give it my read me and the documentation ill be using so it has a clear understanding of my architecture and thought process have it write a plan.md file i will then feed to claude opus 4.8 to create the POC after claude has generated the POC i will feed it to codex 5.5 as i prefer it more for coding task as it has good coding abilities when given the correct instructions, the plan is to use AI as my pair programming buddy writing the code for all this manually is a super power that not most devs have latelly which i dont mind doing but a good developer knows how to leverage the speed of AI to their advantage being able to porpoerly instruct AI and give it a clear context while you have the foundation and fundamentals of programing makes you a good software engineer 
