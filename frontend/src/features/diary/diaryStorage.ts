type PendingDiaryPhoto = {
  uri: string;
  imageData: string | null;
  date: string;
};

let pendingDiaryPhoto: PendingDiaryPhoto | null = null;

export function setPendingDiaryPhoto(photo: PendingDiaryPhoto) {
  pendingDiaryPhoto = photo;
}

export function takePendingDiaryPhoto() {
  const photo = pendingDiaryPhoto;
  pendingDiaryPhoto = null;
  return photo;
}
