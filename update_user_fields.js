db.users.updateMany(
  { "user_id": { "$exists": true } },
  { "$rename": { "user_id": "login_id" } }
);

db.users.find().forEach(function(user) {
  printjson(user);
});
