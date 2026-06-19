import { use } from "react";
import Link from "next/link";
import ChatPageClient from "./ChatPageClient";

interface Props {
  params: Promise<{ courseId: string }>;
}

export default function ChatPage({ params }: Props) {
  // Unwrap params using React.use()
  const { courseId } = use(params);

  return <ChatPageClient courseId={Number(courseId)} />;
}
