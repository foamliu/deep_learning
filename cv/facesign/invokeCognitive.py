
import cognitive_face as CF

KEY = 'cc0014b6b1934e2a92cd32c21de43fdb'  # Replace with a valid subscription key (keeping the quotes in place).
CF.Key.set(KEY)
# If you need to, you can change your base API url with:
CF.BaseUrl.set('https://westcentralus.api.cognitive.microsoft.com/face/v1.0/')

#BASE_URL = 'https://westus.api.cognitive.microsoft.com/face/v1.0/'  # Replace with your regional Base URL
#CF.BaseUrl.set(BASE_URL)

# You can use this example JPG or replace the URL below with your own URL to a JPEG image.
#img_url = 'http://13.65.250.1/image/facesign_0.png'
attributes = (
    'age,gender,headPose,smile,facialHair,glasses,emotion,hair,'
    'makeup,occlusion,accessories,blur,exposure,noise'
)
#faces = CF.face.detect(img_url, False, False, attributes)

img_filename = '../image/facesign_0.png'

faces = CF.face.detect(img_filename, False, False, attributes)
print(faces)
