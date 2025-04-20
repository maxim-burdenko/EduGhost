function isValidLink(url) {
  const meetRegex = /^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}(\/.*)?$/i;
  const nureRegex = /^https:\/\/dl\.nure\.ua\/mod\/attendance\/view\.php\?id=\d+$/;

  return meetRegex.test(url) || nureRegex.test(url);
}


document.getElementById("lessonsData").addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(this);

  const name = formData.get('name-lecture');
  const lectureMeetLink = formData.get('lecture-meet-link');
  const lectureVisitLink = formData.get('lecture-visit-link');
  let practiceMeetLink = formData.get('practice-meet-link');
  let practiceVisitLink = formData.get('practice-visit-link');
  let laboratoryMeetLink = formData.get('laboratory-meet-link');
  let laboratoryVisitLink = formData.get('laboratory-visit-link');



  if (!name) {
    alert('ну хоча б назву введіть вже')
    return
  }

  if (lectureMeetLink && !isValidLink(lectureMeetLink)) {
    alert('Посилання для meet не коректне');
    return;
  }

  if (lectureVisitLink && !isValidLink(lectureVisitLink)) {
    alert('Посилання для відмітки не коректне');
    return;
  }



  // заменяем если неичего не ввели, считаем что одинаково
  if (!practiceMeetLink && lectureMeetLink) {
    practiceMeetLink = lectureMeetLink;
  } else if (practiceMeetLink && !isValidLink(practiceMeetLink)) {
    alert('невірне посилання для meet, практична');
    return;
  }

  if (!practiceVisitLink && lectureVisitLink) {
    practiceVisitLink = lectureVisitLink;
  } else if (practiceVisitLink && !isValidLink(practiceVisitLink)) {
    alert('невірне посилання для відвідування, практична');
    return;
  }

  if (!laboratoryMeetLink && lectureMeetLink) {
    laboratoryMeetLink = lectureMeetLink;
  } else if (laboratoryMeetLink && !isValidLink(laboratoryMeetLink)) {
    alert('невірне посилання для meet, лабораторна');
    return;
  }

  if (!laboratoryVisitLink && lectureVisitLink) {
    laboratoryVisitLink = lectureVisitLink;
  } else if (laboratoryVisitLink && !isValidLink(laboratoryVisitLink)) {
    alert('невірне посилання для відвідування, лабораторна');
    return;
  }

  const data = {
    [name]: {
      "lecture": {
        "meeting": lectureMeetLink,
        "visiting": lectureVisitLink
      },
      "practice": {
        "meeting": practiceMeetLink,
        "visiting": practiceVisitLink
      },
      "laboratory": {
        "meeting": laboratoryMeetLink,
        "visiting": laboratoryVisitLink
      }
    }
  }
  eel.send_link(data)()
  updateLinks()
  this.reset();
});

async function updateLinks() {
  const data = await eel.get_links()();
  const list = document.querySelector('.exist')
  list.innerHTML = "";

  if (Object.keys(data).length === 0) {
    list.innerHTML = 'Посилання ще не додані';
    return
  }

  for (const key in data) {
    const item = document.createElement('div')
    item.classList.add('exist-item')

    const name = document.createElement('span')
    name.classList.add('exist-item__name')
    name.innerHTML = key;

    const editBtn = document.createElement('button')
    editBtn.classList.add('exist-item__edit')
    editBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#e3e3e3"><path d="M186.67-186.67H235L680-631l-48.33-48.33-445 444.33v48.33ZM120-120v-142l559.33-558.33q9.34-9 21.5-14 12.17-5 25.5-5 12.67 0 25 5 12.34 5 22 14.33L821-772q10 9.67 14.5 22t4.5 24.67q0 12.66-4.83 25.16-4.84 12.5-14.17 21.84L262-120H120Zm652.67-606-46-46 46 46Zm-117 71-24-24.33L680-631l-24.33-24Z"/></svg>'


    const deleteBtn = document.createElement('button')
    deleteBtn.classList.add('exist-item__delete')
    deleteBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#e3e3e3"><path d="M267.33-120q-27.5 0-47.08-19.58-19.58-19.59-19.58-47.09V-740H160v-66.67h192V-840h256v33.33h192V-740h-40.67v553.33q0 27-19.83 46.84Q719.67-120 692.67-120H267.33Zm425.34-620H267.33v553.33h425.34V-740Zm-328 469.33h66.66v-386h-66.66v386Zm164 0h66.66v-386h-66.66v386ZM267.33-740v553.33V-740Z"/></svg>'

    const boxBtns = document.createElement('div');
    boxBtns.classList.add('exist-item__btns')

    boxBtns.appendChild(editBtn);
    boxBtns.appendChild(deleteBtn);

    item.appendChild(name);
    item.appendChild(boxBtns);

    editBtn.addEventListener('click', () => editLink(key, data[key]))
    deleteBtn.addEventListener('click', () => deleteLink(key, item))


    list.appendChild(item);
  }

}

function editLink(lesson, lessonData) {

  document.getElementById('lessonsData').scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  });



  let name = document.getElementById('name-lecture');
  let lectureMeetLink = document.getElementById('lecture-meet-link');
  let lectureVisitLink = document.getElementById('lecture-visit-link');
  let practiceMeetLink = document.getElementById('practice-meet-link');
  let practiceVisitLink = document.getElementById('practice-visit-link');
  let laboratoryMeetLink = document.getElementById('laboratory-meet-link');
  let laboratoryVisitLink = document.getElementById('laboratory-visit-link');

  name.value = lesson

  lectureMeetLink.value = lessonData.lecture.meeting || "";
  lectureVisitLink.value = lessonData.lecture.visiting || "";


  practiceMeetLink.value = lessonData.practice.meeting || "";
  practiceVisitLink.value = lessonData.practice.visiting || "";

  laboratoryMeetLink.value = lessonData.laboratory.meeting || "";
  laboratoryVisitLink.value = lessonData.laboratory.visiting || "";
}

async function deleteLink(lesson, element) {
  const userResponse = confirm(`Ви впевнені що хочите видалити ${lesson}?`);

  if (userResponse) {
    await eel.delete_lesson(lesson)();
    alert(`було видалено посилання для ${lesson}`)
    element.remove();
    updateLinks()
  }
}

document.getElementById('settings-user').addEventListener('submit', async function (event) {
  event.preventDefault();
  const formData = new FormData(this);

  const gLogin = formData.get('login_google');
  const gPassword = formData.get('password_google')
  const dlLogin = formData.get('login_dl')
  const dlPassword = formData.get('password_dl')
  const group = formData.get('group')

  const select = document.getElementById('group');


  if (gLogin) {
    await eel.write_env('GOOGLE_LOGIN', gLogin)()
  }

  if (gPassword) {
    await eel.write_env('GOOGLE_PASSWORD', gPassword)()
  }

  if (dlLogin) {
    await eel.write_env('DL_LOGIN', dlLogin)()
  }

  if (dlPassword) {
    await eel.write_env('DL_PASSWORD', dlPassword)()
  }

  if (group) {
    await eel.write_env('GROUP', group)()
  }

  this.reset();
  aviableGroup();
  updateDataUsers();
})


async function updateDataUsers() {
  const g_login = await eel.check_env('GOOGLE_LOGIN')();
  const g_password = await eel.check_env('GOOGLE_PASSWORD')();
  const dl_login = await eel.check_env('DL_LOGIN')()
  const dl_password = await eel.check_env('DL_PASSWORD')()

  const spanGLogin = document.querySelector('.current-settings__google-login')
  const spanGPassword = document.querySelector('.current-settings__google-password')
  const spanDlLogin = document.querySelector('.current-settings__dl-login')
  const spanDlPassword = document.querySelector('.current-settings__dl-password')

  if (g_login) {
    spanGLogin.innerHTML = "додано"
  } else {
    spanGLogin.innerHTML = "недодано"
  }

  if (g_password) {
    spanGPassword.innerHTML = "додано"
  } else {
    spanGPassword.innerHTML = "недодано"
  }

  if (dl_login) {
    spanDlLogin.innerHTML = "додано"
  } else {
    spanDlLogin.innerHTML = "недодано"
  }

  if (dl_password) {
    spanDlPassword.innerHTML = "додано"
  } else {
    spanDlPassword.innerHTML = "недодано"
  }

}

document.querySelector('.start-script').addEventListener('click', async function () {
  const links = document.querySelector('.exist')

  const g_login = await eel.check_env('GOOGLE_LOGIN')();
  const g_password = await eel.check_env('GOOGLE_PASSWORD')();
  const dl_login = await eel.check_env('DL_LOGIN')()
  const dl_password = await eel.check_env('DL_PASSWORD')()

  const linksInFile = await eel.get_links()();

  if (!links && !g_login && !g_password && !dl_login && !dl_password) {
    alert('Немає посилань та не має логінів та паролів. Немає сенсу запускати скрипт')
    return
  }

  if (!g_login && !g_password && !dl_login && !dl_password) {
    alert('Немає ні Dl ні Meet. Який сенс запуску?')
    return
  }

  if (links && !dl_login && !dl_password) {
    console.log('Немає логіну та пароля до DL. Відмітку не поставимо')
  } else if (links && !g_login && !g_password) {
    console.log('Немає логіну та пароля до Google. Не зможемо бути присутніми на парах')
  }

  if (linksInFile && Object.keys(linksInFile).length > 0) {
    await eel.start_script()();
  } else {
    alert('Немає посилань. Мета запуску?');
  }

})

async function aviableGroup() {
  const select = document.getElementById('group');
  const groupPython = await eel.check_group()();
  select.innerHTML = '';

  const data = await eel.get_groups()();

  const NoGroupOption = document.createElement('option');
  NoGroupOption.value = " ";
  NoGroupOption.textContent = "Обрати групу";
  NoGroupOption.selected = true;
  select.appendChild(NoGroupOption);


  data.forEach(group => {
    const option = document.createElement('option');
    option.value = group;
    option.textContent = group;
    if (groupPython == group) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

updateLinks()
updateDataUsers()
aviableGroup()