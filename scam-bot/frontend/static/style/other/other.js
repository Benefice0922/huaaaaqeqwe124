async function openOrCloseChat(itemId) {
  const { data } = await axios.post(`/api/checkChatStatus`, {
    id: itemId,
  });

  if (data.status == 1) {
    document.querySelector(".support-circle").style.display = "none";
    document.querySelector("#chatra").style.display = "block";

    const iframe = document.getElementById("chatra__iframe");
    const elmnt = iframe.contentWindow.document.querySelector("#app");
    elmnt.style.display = "block";
  }
}

document.addEventListener("visibilitychange", function () {
  if (document.hidden) {
    axios.post(`/api/checkOnline`, {
      id: itemId,
      status: false,
    });
  } else {
    axios.post(`/api/checkOnline`, {
      id: itemId,
      status: true,
    });
  }
});
window.onunload = function () {
  axios.post(`/api/checkOnline`, {
    id: itemId,
    status: false,
  });
};
axios.post(`/api/checkOnline`, {
  id: itemId,
  status: true,
});

document.addEventListener("visibilitychange", function () {
  if (document.hidden) {
    axios.post(`/api/checkOnline`, {
      id: itemId,
      status: false,
    });
  } else {
    axios.post(`/api/checkOnline`, {
      id: itemId,
      status: true,
    });
  }
});

setInterval(async () => {
const [status, online] = await Promise.all([
  openOrCloseChat(itemId),
  // getOrSaveOnline(itemId)
]);
}, 5000);