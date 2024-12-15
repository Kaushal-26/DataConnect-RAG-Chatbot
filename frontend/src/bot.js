import ChatBot from "react-chatbotify";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";

// https://react-chatbotify.com/docs/examples/llm_conversation
const callChatBot = async (params, user, org, chat_session_id) => {
  const formData = new FormData();
  formData.append("message", params.userInput);
  formData.append("user_id", user);
  formData.append("org_id", org);
  formData.append("chat_session_id", chat_session_id);

  console.log(params.userInput, user, org, chat_session_id);

  const response = await axios.post("http://localhost:8000/chat", formData);
  params.injectMessage(response.data.message);
};

// https://github.com/tjtanjin/react-chatbotify
export const MyChatBot = ({ user, org }) => {
  const id = uuidv4();

  const flow = {
    start: {
      path: "loop",
    },
    loop: {
      message: async (params) => {
        await callChatBot(params, user, org, id);
      },
      path: "loop",
    },
  };

  // https://react-chatbotify.com/docs/api/settings
  const settings = {
    header: {
      title: (
        <div
          style={{
            cursor: "pointer",
            margin: 0,
            fontSize: 20,
            fontWeight: "bold",
          }}
          onClick={() => window.open("https://github.com/Kaushal-26/")}
        >
          Chatbot with your loaded data
        </div>
      ),
      showAvatar: true,
    },
    tooltip: {
      mode: "CLOSE",
      text: "Talk to your data! 🤖",
    },
  };

  return <ChatBot id={id} flow={flow} settings={settings} />;
};
