import { use } from "react";
import Link from "next/link";
import CourseDetailPageClient from "./CourseDetailPageClient";

interface Props {
  params: Promise<{ courseId: string }>;
}

export default function CourseDetailPage({ params }: Props) {
  // Unwrap params using React.use()
  const { courseId } = use(params);

  return <CourseDetailPageClient courseId={Number(courseId)} />;
}
