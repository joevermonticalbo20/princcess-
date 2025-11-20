// Load data.json
fetch("data.json")
  .then(res => res.json())
  .then(data => {
    const regionSelect = document.getElementById("region");
    const provinceSelect = document.getElementById("province");
    const citySelect = document.getElementById("city");
    const barangaySelect = document.getElementById("barangay");
    const zipcodeInput = document.getElementById("zipcode");

    // Populate regions
    regionSelect.innerHTML = `<option value="">Select Region</option>`;
    Object.keys(data).forEach(region => {
      regionSelect.innerHTML += `<option value="${region}">${region}</option>`;
    });

    regionSelect.addEventListener("change", () => {
      provinceSelect.innerHTML = `<option value="">Select Province</option>`;
      citySelect.innerHTML = `<option value="">Select City/Municipality</option>`;
      barangaySelect.innerHTML = `<option value="">Select Barangay</option>`;
      zipcodeInput.value = "";

      if (regionSelect.value) {
        Object.keys(data[regionSelect.value]).forEach(province => {
          provinceSelect.innerHTML += `<option value="${province}">${province}</option>`;
        });
      }
    });

    provinceSelect.addEventListener("change", () => {
      citySelect.innerHTML = `<option value="">Select City/Municipality</option>`;
      barangaySelect.innerHTML = `<option value="">Select Barangay</option>`;
      zipcodeInput.value = "";

      if (provinceSelect.value) {
        Object.keys(data[regionSelect.value][provinceSelect.value]).forEach(city => {
          citySelect.innerHTML += `<option value="${city}">${city}</option>`;
        });
      }
    });

    citySelect.addEventListener("change", () => {
      barangaySelect.innerHTML = `<option value="">Select Barangay</option>`;
      zipcodeInput.value = "";

      if (citySelect.value) {
        Object.keys(data[regionSelect.value][provinceSelect.value][citySelect.value]).forEach(brgy => {
          barangaySelect.innerHTML += `<option value="${brgy}">${brgy}</option>`;
        });
      }
    });

    barangaySelect.addEventListener("change", () => {
      if (barangaySelect.value) {
        zipcodeInput.value =
          data[regionSelect.value][provinceSelect.value][citySelect.value][barangaySelect.value];
      } else {
        zipcodeInput.value = "";
      }
    });
  });

// Auto-calculate age
document.getElementById("dob").addEventListener("change", function () {
  const birthDate = new Date(this.value);
  const ageInput = document.getElementById("age");
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  ageInput.value = age;
});
