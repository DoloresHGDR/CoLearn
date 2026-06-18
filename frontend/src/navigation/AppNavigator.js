import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import ChatScreen from "../screens/ChatScreen";
import CreateClassScreen from "../screens/CreateClassScreen";
import HomeScreen from "../screens/HomeScreen";
import JoinClassScreen from "../screens/JoinClassScreen";
import LoginScreen from "../screens/LoginScreen";
import MetricsScreen from "../screens/MetricsScreen";
import RegisterScreen from "../screens/RegisterScreen";
import TeacherQuestionsScreen from "../screens/TeacherQuestionsScreen";
import WelcomeScreen from "../screens/WelcomeScreen";

const Stack = createStackNavigator();

// Todas las pantallas usan TopBar custom, sin header nativo.
export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Welcome" screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Welcome" component={WelcomeScreen} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="CreateClass" component={CreateClassScreen} />
        <Stack.Screen name="JoinClass" component={JoinClassScreen} />
        <Stack.Screen name="Chat" component={ChatScreen} />
        <Stack.Screen name="Metrics" component={MetricsScreen} />
        <Stack.Screen name="TeacherQuestions" component={TeacherQuestionsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
