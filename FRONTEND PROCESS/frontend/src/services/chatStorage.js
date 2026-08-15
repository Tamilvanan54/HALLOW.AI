export const saveMessages = (
  chatId,
  messages
) => {
  const email =
    localStorage.getItem("email");

  localStorage.setItem(
    `chat_${email}_${chatId}`,
    JSON.stringify(messages)
  );
};

export const loadMessages = (
  chatId
) => {
  const email =
    localStorage.getItem("email");

  const data =
    localStorage.getItem(
      `chat_${email}_${chatId}`
    );

  return data
    ? JSON.parse(data)
    : [];
};

export const deleteMessages = (
  chatId
) => {
  const email =
    localStorage.getItem("email");

  localStorage.removeItem(
    `chat_${email}_${chatId}`
  );
};