
adb uninstall com.dan106.dev
cd android && ./gradlew clean
cd android && ./gradlew clean && cd .. && npx expo run:android

node_modules\@azesmway\react-native-unity\android\src\main\java\com\azesmwayreactnativeunity\UPlayer.java
<!-- 之前 -->
    public FrameLayout requestFrame() throws NoSuchMethodException {
        try {
            Method getFrameLayout = unityPlayer.getClass().getMethod("getFrameLayout");
            return (FrameLayout) getFrameLayout.invoke(unityPlayer);
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            // Create a new FrameLayout and add the UnityPlayer to it
               return unityPlayer;
        }
    }
<!-- 之后 -->
    public FrameLayout requestFrame() throws NoSuchMethodException {
        try {
            Method getFrameLayout = unityPlayer.getClass().getMethod("getFrameLayout");
            return (FrameLayout) getFrameLayout.invoke(unityPlayer);
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            // Create a new FrameLayout and add the UnityPlayer to it
            FrameLayout frameLayout = new FrameLayout(unityPlayer.getContext());
            frameLayout.addView(unityPlayer);
            return frameLayout;
        }
    }


    
<!-- 之后 -->
    public FrameLayout requestFrame() throws NoSuchMethodException {
        try {
            // Try to get the FrameLayout directly from UnityPlayer
            if (unityPlayer instanceof FrameLayout) {
                return (FrameLayout) unityPlayer;
            }
            
            // If not directly a FrameLayout, try to get it through reflection
            Method getFrameLayout = unityPlayer.getClass().getMethod("getFrameLayout");
            Object result = getFrameLayout.invoke(unityPlayer);
            if (result instanceof FrameLayout) {
                return (FrameLayout) result;
            }
            
            // If we can't get a FrameLayout, create one and add the UnityPlayer
            FrameLayout frameLayout = new FrameLayout(unityPlayer.getContext());
            frameLayout.addView(unityPlayer);
            return frameLayout;
        } catch (Exception e) {
            // If all else fails, create a new FrameLayout
            FrameLayout frameLayout = new FrameLayout(unityPlayer.getContext());
            frameLayout.addView(unityPlayer);
            return frameLayout;
        }
    }



    public Object getParentPlayer() throws NoSuchMethodException, InvocationTargetException, IllegalAccessException {
        try {
            FrameLayout frame = this.requestFrame();
            return frame.getParent();
        } catch (Exception e) {
            Method getParent = unityPlayer.getClass().getMethod("getParent");
            return getParent.invoke(unityPlayer);
        }
    }


    patches\@azesmway+react-native-unity+1.0.0.patch

    diff --git a/node_modules/@azesmway/react-native-unity/android/src/main/java/com/azesmwayreactnativeunity/UPlayer.java b/node_modules/@azesmway/react-native-unity/android/src/main/java/com/azesmwayreactnativeunity/UPlayer.java
index xxxxxxx..xxxxxxx 100644
--- a/node_modules/@azesmway/react-native-unity/android/src/main/java/com/azesmwayreactnativeunity/UPlayer.java
+++ b/node_modules/@azesmway/react-native-unity/android/src/main/java/com/azesmwayreactnativeunity/UPlayer.java
@@ -97,7 +97,12 @@ public class UPlayer {
     public FrameLayout requestFrame() throws NoSuchMethodException {
         try {
             Method getFrameLayout = unityPlayer.getClass().getMethod("getFrameLayout");
-            return (FrameLayout) getFrameLayout.invoke(unityPlayer);
+            Object result = getFrameLayout.invoke(unityPlayer);
+            if (result instanceof FrameLayout) {
+                return (FrameLayout) result;
+            }
+            FrameLayout frameLayout = new FrameLayout(unityPlayer.getContext());
+            frameLayout.addView(unityPlayer);
+            return frameLayout;
         } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
             FrameLayout frameLayout = new FrameLayout(unityPlayer.getContext());
             frameLayout.addView(unityPlayer);


npx patch-package @azesmway/react-native-unity


  public FrameLayout requestFrame() throws NoSuchMethodException {
        try {
            Method getFrameLayout = unityPlayer.getClass().getMethod("getFrameLayout");
            Object result = getFrameLayout.invoke(unityPlayer);
            if (result instanceof FrameLayout) {
                return (FrameLayout) result;
            }
            throw new NoSuchMethodException("UnityPlayer.getFrameLayout() did not return a FrameLayout");
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            throw new NoSuchMethodException("Failed to get FrameLayout: " + e.getMessage());
        }
    }